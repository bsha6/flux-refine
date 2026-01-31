# Flashcard Assistant Pipeline

## Goal (high level)

Build a **flashcard assistant pipeline** that:

1. **Reads from Anki** — Exports or syncs your existing Anki flashcards so the pipeline can work with them (e.g. CSV export, scheduled via CronJob).
2. **Updates flagged cards** — Uses **n8n** (running in Docker) to process cards you’ve flagged in Anki: refine, fix, or improve them (e.g. with a stronger API/key and good prompting).
3. **Adds new flashcards** — Generates new cards from the pipeline output and writes them to a shared location (e.g. volume bind) so a Python script can import them into Anki while preserving history.
4. **Supports multiple content sources** — Eventually extend beyond “flag-based” flow to create cards from:
   - **YouTube scripts** (transcripts / scripts → flashcards)
   - **Articles** (interesting articles → flashcards)
   - Other topics you define later.

So: **Anki ↔ pipeline (n8n + scripts) ↔ multiple inputs (flags, YouTube, articles)** with a single “import back into Anki” path that keeps history intact.

## Run Scripts
Use UV: `uv run python paths.py`

Run docker compose from the project root so `./flashcard_exchange` resolves correctly.

---

# TODO's:

- Check in to git

## Data pipeline:

- Create pipeline for writing CSV from Anki.
- Connect using CronJob to run this pipeline regularly.
- Test input from pipeline in N8n Docker container, starting with just processing or refining flagged cards.
- **CSV in n8n:** Use a **Code** node (not Extract from File) to parse the Anki export CSV: read file as UTF-8 text and parse with a library that supports quoted newlines (e.g. Node `csv-parse` or Papa Parse). n8n’s default CSV node fails on multi-line cells (“Invalid Record Length” / “Invalid Opening Quote”).
- Test some sort of more powerful API key with refining the flag cards (we'll need to do some prompting here).
- Test just writing a few of these cards to the volume bind in a separate folder with maybe a different file nomenclature.
- Python script to read from the volume bind mount and import into Anki while preserving history.