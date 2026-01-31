"""
I/O utilities for reading/writing delimited files in the flashcard exchange bind mount.

Pipeline uses TSV (tab-separated) to avoid comma/newline parsing issues in n8n and elsewhere.
CSV read/write kept for backward compatibility with existing anki_export_*.csv files.

Reusable by:
- export_anki_to_csv.py (writes anki_export_<datetime>.tsv)
- Future import script (reads anki_refined_*.tsv / import_*.tsv)
"""

import csv
from pathlib import Path
from typing import Any, Iterator

from tsv_parsing.paths import (
    get_exchange_dir,
    EXPORT_PREFIX,
    REFINED_PREFIX,
    IMPORT_PREFIX,
)

# Consistent encoding for round-trip
CSV_ENCODING = "utf-8"
CSV_DIALECT = "excel"

# TSV: tabs are rare in card text, so fewer quoting/parsing issues than CSV
TSV_DELIMITER = "\t"
TSV_EXT = ".tsv"


def ensure_exchange_dir() -> Path:
    """Create the exchange directory if it does not exist; return its path."""
    d = get_exchange_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_export_csvs() -> list[Path]:
    """List CSV files in the exchange dir that are full Anki exports (anki_export_*.csv)."""
    return sorted(get_exchange_dir().glob(f"{EXPORT_PREFIX}*.csv"))


def list_export_tsvs() -> list[Path]:
    """List TSV files in the exchange dir that are full Anki exports (anki_export_*.tsv)."""
    return sorted(get_exchange_dir().glob(f"{EXPORT_PREFIX}*{TSV_EXT}"))


def list_refined_csvs() -> list[Path]:
    """List CSV files that have been refined/edited and are ready for re-import."""
    d = get_exchange_dir()
    refined = list(d.glob(f"{REFINED_PREFIX}*.csv")) + list(d.glob(f"{IMPORT_PREFIX}*.csv"))
    return sorted(set(refined))


def list_refined_tsvs() -> list[Path]:
    """List TSV files that have been refined/edited and are ready for re-import."""
    d = get_exchange_dir()
    refined = list(d.glob(f"{REFINED_PREFIX}*{TSV_EXT}")) + list(d.glob(f"{IMPORT_PREFIX}*{TSV_EXT}"))
    return sorted(set(refined))


def read_csv_rows(
    path: Path,
    *,
    encoding: str = CSV_ENCODING,
    dialect: str = CSV_DIALECT,
) -> Iterator[dict[str, str]]:
    """
    Read a CSV file and yield rows as dicts (first row = headers).

    Use this when reading refined/import CSVs so parsing is consistent.
    """
    with path.open(encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            yield row


def read_tsv_rows(
    path: Path,
    *,
    encoding: str = CSV_ENCODING,
) -> Iterator[dict[str, str]]:
    """
    Read a TSV file and yield rows as dicts (first row = headers).

    Use for pipeline files; avoids comma/newline parsing issues.
    """
    with path.open(encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=TSV_DELIMITER, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield row


def write_csv(
    path: Path,
    headers: list[str],
    rows: Iterator[dict[str, Any]],
    *,
    encoding: str = CSV_ENCODING,
    dialect: str = CSV_DIALECT,
    extrasaction: str = "ignore",
    quote_all: bool = False,
) -> None:
    """
    Write CSV with the given headers and rows (dicts).

    Uses same encoding/dialect as read_csv_rows for round-trip consistency.
    If quote_all is True, all non-numeric fields are quoted (e.g. for exports
    where guids or text should be unambiguous).
    """
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            dialect=dialect,
            extrasaction=extrasaction,
            quoting=csv.QUOTE_NONNUMERIC if quote_all else csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(
    path: Path,
    headers: list[str],
    rows: Iterator[dict[str, Any]],
    *,
    encoding: str = CSV_ENCODING,
    extrasaction: str = "ignore",
) -> None:
    """
    Write TSV with the given headers and rows (dicts).

    Uses tab as delimiter; fields containing tab/newline are quoted automatically.
    Prefer over CSV for pipeline files to avoid comma/newline parsing issues in n8n.
    """
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            delimiter=TSV_DELIMITER,
            extrasaction=extrasaction,
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)
