"""
Local test script for build_taste_profile.

Run this from inside the 'lambda' folder with:
    python test_build_taste_profile.py
"""

import json
from build_taste_profile import build_taste_profile


def main():
    # This simulates the "items" portion of an event
    sample_items = {
        "user_id": "spotify:user:briana",
        "top_artists": [
            "NCT 127",
            "Taeyeon",
            "Red Velvet",
            "NewJeans",
        ],
        "top_genres": [
            "k-pop",
            "k-pop",
            "k-pop",
            "r&b",
            "pop",
        ],
        "top_tracks": [
            "Favorite – NCT 127",
            "Sticker – NCT 127",
            "Kick It – NCT 127",
            "Track A – Taeyeon",
            "Track B – Red Velvet",
        ],
    }

    profile = build_taste_profile(sample_items)

    print("=== Built Taste Profile ===")
    print(json.dumps(profile, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
