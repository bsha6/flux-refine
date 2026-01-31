"""
Reusable utilities for CSV flashcard exchange between Anki and the pipeline (n8n).

- Export: script writes anki_export_<datetime>.tsv to the bind mount.
- Import: pipeline/n8n writes refined/edited TSVs (anki_refined_*.tsv or import_*.tsv);
  Python import script reads from the bind mount using these utilities.

CSV helpers (list_export_csvs, list_refined_csvs, read_csv_rows, write_csv) are kept
for reading legacy anki_export_*.csv files only.
"""

from tsv_parsing.constants import DECK_ID_TO_TOPIC
from tsv_parsing.paths import (
    get_exchange_dir,
    EXPORT_PREFIX,
    REFINED_PREFIX,
    IMPORT_PREFIX,
)
from tsv_parsing.io_utils import (
    ensure_exchange_dir,
    list_export_tsvs,
    list_refined_tsvs,
    read_tsv_rows,
    write_tsv,
    list_export_csvs,
    list_refined_csvs,
    read_csv_rows,
    write_csv,
)

__all__ = [
    "DECK_ID_TO_TOPIC",
    "get_exchange_dir",
    "EXPORT_PREFIX",
    "REFINED_PREFIX",
    "IMPORT_PREFIX",
    "ensure_exchange_dir",
    "list_export_tsvs",
    "list_refined_tsvs",
    "read_tsv_rows",
    "write_tsv",
    "list_export_csvs",
    "list_refined_csvs",
    "read_csv_rows",
    "write_csv",
]
