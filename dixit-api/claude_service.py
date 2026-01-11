"""
AI service for Dixit game.

Uses pre-generated card descriptions and clues for AI player decisions.
"""

import json
import random
from pathlib import Path


# Load pre-generated data at module level
CARD_DESCRIPTIONS = {}
CARD_CLUES = {}


def load_card_data():
    """Load pre-generated card descriptions and clues from JSON files."""
    global CARD_DESCRIPTIONS, CARD_CLUES

    base_path = Path(__file__).parent

    desc_path = base_path / "card_descriptions.json"
    if desc_path.exists():
        with open(desc_path, 'r') as f:
            CARD_DESCRIPTIONS = json.load(f)
        print(f"Loaded {len(CARD_DESCRIPTIONS)} card descriptions")
    else:
        print("Warning: card_descriptions.json not found")

    clues_path = base_path / "card_clues.json"
    if clues_path.exists():
        with open(clues_path, 'r') as f:
            CARD_CLUES = json.load(f)
        print(f"Loaded clues for {len(CARD_CLUES)} cards")
    else:
        print("Warning: card_clues.json not found")


def generate_narrator_clue(card_id: int) -> str:
    """
    Get a creative clue for the narrator's card from pre-generated data.

    Args:
        card_id: The ID of the card image (1-135)

    Returns:
        A creative clue phrase
    """
    card_key = str(card_id)

    if card_key in CARD_CLUES and CARD_CLUES[card_key]:
        return random.choice(CARD_CLUES[card_key])

    # Fallback clues if card not found
    fallbacks = [
        "Dreams within dreams", "The hidden path", "Whispers of time",
        "Between worlds", "Silent echoes", "The forgotten door",
        "Mysterious journey", "Beyond the veil", "Secret garden", "Lost in thought",
        "E motion", "Chasing shadows", "Wings of imagination", "Colors of the mind",
    ]
    return random.choice(fallbacks)


def get_card_description(card_id: int) -> str:
    """Get the description for a card."""
    card_key = str(card_id)
    return CARD_DESCRIPTIONS.get(card_key, f"Card {card_id}")


def select_best_card(phrase: str, card_descriptions: dict) -> int:
    """
    Select a card that could plausibly match the narrator's phrase.

    Uses simple keyword matching to find relevant cards.

    Args:
        phrase: The narrator's clue phrase
        card_descriptions: Dict mapping card_id (int) to description (str)

    Returns:
        The card ID to play
    """
    if not card_descriptions:
        raise ValueError("No cards available to select from")

    phrase_lower = phrase.lower()
    phrase_words = set(phrase_lower.split())

    # Score each card based on keyword overlap
    scores = {}
    for card_id, description in card_descriptions.items():
        desc_lower = description.lower()
        desc_words = set(desc_lower.split())

        # Count matching words
        common_words = phrase_words & desc_words
        # Also check if phrase is contained in description
        phrase_in_desc = phrase_lower in desc_lower

        score = len(common_words) + (3 if phrase_in_desc else 0)
        scores[card_id] = score

    # Find cards with highest scores
    max_score = max(scores.values()) if scores else 0

    if max_score > 0:
        # Pick randomly among top scoring cards
        top_cards = [cid for cid, score in scores.items() if score == max_score]
        return random.choice(top_cards)
    else:
        # No matches found, pick randomly
        return random.choice(list(card_descriptions.keys()))


def vote_for_card(phrase: str, card_descriptions: dict) -> int:
    """
    Vote for the card most likely to be the narrator's card.

    Uses the same logic as select_best_card since both need to find
    cards matching the phrase.

    Args:
        phrase: The narrator's clue phrase
        card_descriptions: Dict mapping card_id (int) to description (str)

    Returns:
        The card ID to vote for
    """
    return select_best_card(phrase, card_descriptions)


# Load data when module is imported
load_card_data()
