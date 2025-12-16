"""
test_lambda_locally.py

Local test for the Lambda handler.

Run with:
    python test_lambda_locally.py
"""

import json
from handler import lambda_handler


def main():
    # This simulates the event object Lambda receives
    event = {
        "items": {
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
                "Moonlight – NCT 127",
                "Track A – Taeyeon",
                "Track B – Red Velvet",
            ],
        }
    }

    response = lambda_handler(event, context=None)

    print("=== Lambda Response ===")
    print("Status code:", response.get("statusCode"))
    print("Headers:", response.get("headers"))
    print("Body JSON:")
    try:
        body = json.loads(response.get("body", "{}"))
        print(json.dumps(body, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(response.get("body"))


if __name__ == "__main__":
    main()
