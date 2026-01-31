"""
Paths for the flashcard exchange volume bind mount.

Matches docker-compose volume:
  host: <project>/flashcard_exchange  ->  container: /flashcards

Scripts running on the host use the project-local path; CronJob/container can
set FLASHCARD_EXCHANGE_DIR to /flashcards.
"""

import os
from pathlib import Path

# Default: project dir / flashcard_exchange (same as docker-compose bind)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_EXCHANGE = _PROJECT_ROOT / "flashcard_exchange"

# Env override for CronJob or when running inside container
EXCHANGE_DIR_ENV = "FLASHCARD_EXCHANGE_DIR"

# File nomenclature for pipeline stages
EXPORT_PREFIX = "anki_export_"   # Full export from Anki; dated/versioned
REFINED_PREFIX = "anki_refined_"  # Edited/refined by n8n; ready for re-import
IMPORT_PREFIX = "import_"         # Alternative prefix for files to import


def get_exchange_dir() -> Path:
    """Return the flashcard exchange directory (bind mount on host or in container)."""
    path = os.environ.get(EXCHANGE_DIR_ENV)
    if path:
        return Path(path)
    return _DEFAULT_EXCHANGE
