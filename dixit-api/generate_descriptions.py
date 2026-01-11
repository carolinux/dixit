#!/usr/bin/env python3
"""
One-time script to generate text descriptions for all Dixit card images.
These descriptions are used by AI players to select cards without needing
to call the Vision API for every move.

Usage:
    ANTHROPIC_API_KEY=your_key python generate_descriptions.py
"""

import anthropic
import base64
import json
import os
import time
from pathlib import Path


def generate_all_descriptions():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    client = anthropic.Anthropic(api_key=api_key)
    descriptions = {}

    # Path to card images
    cards_path = Path(__file__).parent.parent / "dixit-web" / "public" / "resources" / "pictures" / "cards" / "medusa"

    for card_num in range(1, 136):
        image_path = cards_path / f"{card_num}.jpg"

        if not image_path.exists():
            print(f"Warning: Card {card_num} not found at {image_path}")
            continue

        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Describe this Dixit card image in 2-3 sentences.
Focus on the key visual elements, mood, colors, and any symbolic meanings.
This description will be used by an AI to play the game Dixit."""
                        }
                    ]
                }]
            )

            descriptions[str(card_num)] = message.content[0].text.strip()
            print(f"Generated description for card {card_num}")

        except Exception as e:
            print(f"Error generating description for card {card_num}: {e}")
            descriptions[str(card_num)] = f"Card {card_num} - description unavailable"

        # Rate limiting - be gentle with the API
        time.sleep(0.5)

    # Save to JSON file
    output_path = Path(__file__).parent / "card_descriptions.json"
    with open(output_path, 'w') as f:
        json.dump(descriptions, f, indent=2)

    print(f"\nGenerated {len(descriptions)} descriptions")
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    generate_all_descriptions()
