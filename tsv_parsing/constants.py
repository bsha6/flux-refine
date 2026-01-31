"""
Global constants for flashcard pipeline (deck metadata, etc.).
"""

# Anki deck ID (string) -> human-readable deck name / topic.
# Used for the deck_name column in anki_export_*.csv when Anki's decks JSON isn't available.
# Edit this dict to add or change deck names; add new deck IDs as you see them in exports.
DECK_ID_TO_TOPIC: dict[str, str] = {
    "1": "coding interview",
    "1739772684427": "system design",
    "1741887251948": "Data Science and AI/ML",
    "1742873485370": "DevOps and Kubernetes",
    "1743381791968": "English Vocab",
    "1744125521824": "Primer",
}
