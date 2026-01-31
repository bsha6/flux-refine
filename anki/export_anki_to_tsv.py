#!/usr/bin/env python3
"""
Export all Anki flashcards from all decks to a dated TSV in the flashcard exchange
bind mount (same path used by docker-compose for n8n). TSV avoids comma/newline parsing issues.

Usage:
  python scripts/export_anki_to_tsv.py
  FLASHCARD_EXCHANGE_DIR=/flashcards python scripts/export_anki_to_tsv.py  # in container

Optional env:
  ANKI_PROFILE       – profile name (default: first profile in Anki2 folder)
  ANKI_COLLECTION    – full path to collection.anki2/.anki21 (overrides profile)
  FLASHCARD_EXCHANGE_DIR – output directory (default: project/flashcard_exchange)

Deck:
  deck column is resolved from tsv_parsing.constants.DECK_ID_TO_TOPIC (deck id -> name).
  Edit that constant to add or change human-readable deck names.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root on path for local imports (run from repo root or scripts/)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from tsv_parsing.constants import DECK_ID_TO_TOPIC  # noqa: E402
from tsv_parsing.io_utils import TSV_EXT, ensure_exchange_dir, write_tsv  # noqa: E402
from tsv_parsing.paths import EXPORT_PREFIX  # noqa: E402

# Anki stores note fields separated by ASCII unit separator
ANKI_FIELD_SEP = "\x1f"

# macOS default Anki location
ANKI2_BASE = Path.home() / "Library" / "Application Support" / "Anki2"


def find_collection_path() -> Path:
    """Resolve path to collection.anki21 or collection.anki2."""
    explicit = os.environ.get("ANKI_COLLECTION")
    if explicit:
        p = Path(explicit)
        if p.exists():
            return p
        raise FileNotFoundError(f"ANKI_COLLECTION not found: {p}")

    profile = os.environ.get("ANKI_PROFILE")
    if profile:
        base = ANKI2_BASE / profile
    else:
        if not ANKI2_BASE.exists():
            raise FileNotFoundError(
                f"Anki data not found at {ANKI2_BASE}. "
                "Set ANKI_COLLECTION or ANKI_PROFILE, or install Anki."
            )
        # Use first profile directory (e.g. "User 1")
        profiles = [d for d in ANKI2_BASE.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if not profiles:
            raise FileNotFoundError(f"No profile found under {ANKI2_BASE}")
        base = sorted(profiles)[0]

    for name in ("collection.anki21", "collection.anki2"):
        path = base / name
        if path.exists():
            return path
    raise FileNotFoundError(f"No collection.anki21/anki2 in {base}")


def export_all_to_tsv(
    conn: sqlite3.Connection,
    out_path: Path,
    *,
    write_tsv,
) -> int:
    """
    Export all notes from all decks to TSV. Returns number of rows written.
    deck comes from tsv_parsing.constants.DECK_ID_TO_TOPIC (fallback: deck id).
    """
    row = conn.execute("SELECT models FROM col").fetchone()
    models_json = row[0]

    def _parse_col_json(raw) -> dict:
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    models = _parse_col_json(models_json)

    # Model id -> field names (in order)
    model_fields: dict[int, list[str]] = {}
    for mid_str, m in models.items():
        mid = int(mid_str)
        model_fields[mid] = [f["name"] for f in sorted(m["flds"], key=lambda x: x["ord"])]

    # Resolve deck name: DECK_ID_TO_TOPIC constant first, else deck id as string
    resolved_deck_names: dict[int, str] = {}
    for nid, did in conn.execute("SELECT nid, did FROM cards"):
        if did not in resolved_deck_names:
            resolved_deck_names[did] = DECK_ID_TO_TOPIC.get(str(did), str(did))

    # Note id -> resolved deck name (from first card)
    note_deck: dict[int, str] = {}
    for nid, did in conn.execute("SELECT nid, did FROM cards"):
        if nid not in note_deck:
            note_deck[nid] = resolved_deck_names.get(did, str(did))

    # Note id -> flag (from first card; Anki flags 0–7, 0 = none)
    note_flag: dict[int, int] = {}
    for nid, flags in conn.execute("SELECT nid, flags FROM cards"):
        if nid not in note_flag:
            note_flag[nid] = flags

    # Base TSV columns (stable for round-trip / import)
    base_headers = ["guid", "deck", "note_type", "note_id", "tags", "flag"]

    # Collect all rows; we need to know all possible field names across models
    all_field_names: set[str] = set()
    rows_data: list[tuple[dict[str, str], list[str]]] = []  # (base_dict, field_values)

    for nid, guid, mid, tags, flds in conn.execute(
        "SELECT id, guid, mid, tags, flds FROM notes"
    ):
        deck = note_deck.get(nid, "")
        field_names = model_fields.get(mid, [])
        model = models.get(str(mid), {})
        note_type = model.get("name", str(mid))

        values = flds.split(ANKI_FIELD_SEP) if flds else []
        # When models JSON was missing/invalid we have no field names; use fallback so content is still exported
        if not field_names and values:
            field_names = (
                ["Front", "Back"]
                if len(values) == 2
                else [f"field_{i}" for i in range(len(values))]
            )
        all_field_names.update(field_names)

        base = {
            "guid": guid,
            "deck": deck,
            "note_type": note_type,
            "note_id": str(nid),
            "tags": (tags or "").strip(),
            "flag": str(note_flag.get(nid, 0)),
        }
        # Field values by name (same order as model)
        field_vals = [values[i] if i < len(values) else "" for i in range(len(field_names))]
        rows_data.append((base, field_names, field_vals))

    # Build header: base + all field names (front then back, then rest alphabetically)
    preferred_field_order = ["Front", "Back"]
    field_header = [n for n in preferred_field_order if n in all_field_names]
    field_header += sorted(n for n in all_field_names if n not in preferred_field_order)
    headers = base_headers + field_header

    def row_iter():
        for base, field_names, field_vals in rows_data:
            row = dict(base)
            for name, val in zip(field_names, field_vals):
                row[name] = val
            yield row

    write_tsv(out_path, headers, row_iter())
    return len(rows_data)


def main() -> None:
    try:
        coll_path = find_collection_path()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Dated filename: anki_export_2025-01-30T14-30-00.tsv (TSV avoids comma/newline parsing issues)
    now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    exchange = ensure_exchange_dir()
    out_path = exchange / f"{EXPORT_PREFIX}{now}{TSV_EXT}"

    conn = sqlite3.connect(str(coll_path))
    try:
        count = export_all_to_tsv(conn, out_path, write_tsv=write_tsv)
    finally:
        conn.close()

    print(f"Exported {count} notes to {out_path}")


if __name__ == "__main__":
    main()
