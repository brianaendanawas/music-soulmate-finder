import json
import os
from datetime import datetime, timezone

from .spotify_client import create_spotify_client
from .taste_profile import build_taste_profile


def main():
    sp = create_spotify_client()

    # Identify current user
    user = sp.current_user()
    user_id = user.get("id") or "unknown-user"

    # Build taste profile
    taste_profile = build_taste_profile(sp)

    # pk/sk design
    pk = f"USER#{user_id}"
    sk = "TASTE_PROFILE#CURRENT"

    now_iso = datetime.now(timezone.utc).isoformat()

    item = {
        "pk": pk,
        "sk": sk,
        "user_id": user_id,
        "generated_at": now_iso,
        "taste_profile": taste_profile,
    }

    # Save to data/
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"taste_profile_{user_id}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)

    print(f"Saved taste profile item to: {output_path}")
    print(json.dumps(item, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
