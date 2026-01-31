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

## Data pipeline:

- Create pipeline for writing TSV from Anki.
- Connect using CronJob to run this pipeline regularly.
- Test input from pipeline in N8n Docker container, starting with just processing or refining flagged cards.
- **CSV in n8n:** Use a **Code** node (not Extract from File) to parse the Anki export CSV: read file as UTF-8 text and parse with a library that supports quoted newlines (e.g. Node `csv-parse` or Papa Parse). n8n’s default CSV node fails on multi-line cells (“Invalid Record Length” / “Invalid Opening Quote”).
- Test some sort of more powerful API key with refining the flag cards (we'll need to do some prompting here).
- Test just writing a few of these cards to the volume bind in a separate folder with maybe a different file nomenclature.
- Python script to read from the volume bind mount and import into Anki while preserving history.


## Phase 1: Refining Existing Cards (The "Quality First" Loop)

**Goal:** Automate the improvement of cards you've manually flagged as "hard" or "confusing" in Anki.

- [ ] **Define the "Refine" Trigger:** In Anki, decide on a specific flag (e.g., Red Flag) or a tag (e.g., `refine-me`) that signals a card needs help.
- [ ] **The Python "Export" Logic:** Update your script to only export cards with that specific flag/tag.
  - **Crucial:** You must export the Note ID.
- [ ] **n8n Refinement Workflow:**
  - **Input:** Read the exported TSV.
  - **LLM Prompt:** "Rewrite this flashcard to follow the Minimum Information Principle. Break complex cards into two. Keep the same context."
  - **Output:** Write to `refined_cards.tsv`.
- [ ] **The Sync-Back Script:** Write a Python script (using AnkiConnect) that reads `refined_cards.tsv` and updates the existing notes by Note ID.

## Phase 2: Web Integration & Staging (The "Safety Valve")

**Goal:** Ingest new data without direct-importing, giving you a chance to review cards before they hit your deck.

- [ ] **Create the "Staging" Infrastructure:**
  - **Option A (The Anki Way):** Create a dedicated Anki Deck named `00_INBOX`. Cards go here first for a manual "Move to Main Deck" review.
  - **Option B (The n8n Way):** Use a Google Sheet or an n8n-hosted "Binary" file as a queue you can glance at.
- [ ] **Build the YouTube/Article Trigger:**
  - **YouTube:** Create an n8n webhook that accepts a URL. Use the YouTube node to fetch the transcript.
  - **Articles:** Set up an n8n webhook and use a "Push to Webhook" browser extension (like Webview or n8n's own Chrome extension) to send page content.
- [ ] **Implement Content Hashing (Deduplication Lite):**
  - Before processing an article, generate an MD5 hash of the URL.
  - Store this hash in a local `processed_sources.csv`.
  - If the hash exists, stop the workflow to prevent duplicate cards.

## Phase 3: Vector DB (The "Brain Mirror")

**Goal:** Use semantic search to identify gaps and perform high-level deduplication.

- [ ] **Deploy Qdrant via Docker:** Add a qdrant service to your `docker-compose.yaml`.
- [ ] **The "Index" Workflow:** Create an n8n workflow that periodically pulls all your current Anki cards, generates embeddings (via OpenAI or Ollama), and stores them in Qdrant.
- [ ] **The "Gap Check" Logic:** When an article is processed, instead of just checking the URL hash, query Qdrant: "Is this concept already covered in my deck?" Only generate a card if the "Similarity Score" is below a certain threshold (e.g., 0.7).