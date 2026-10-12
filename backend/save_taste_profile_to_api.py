import json
import os

import requests
from dotenv import load_dotenv

from .spotify_client import create_spotify_client
from .taste_profile import collect_spotify_profile_data


def main():
    load_dotenv()

    api_base_url = os.getenv("AWS_API_BASE_URL")

    if not api_base_url:
        raise RuntimeError(
            "Missing AWS_API_BASE_URL. Add it to your .env file."
        )

    api_base_url = api_base_url.rstrip("/")
    save_url = f"{api_base_url}/taste-profile"

    sp = create_spotify_client()

    # Collect the raw Spotify data expected by the AWS profile builder.
    payload = collect_spotify_profile_data(sp)

    print("\n=== Spotify data that will be sent to AWS ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    print("\n=== Safety check ===")
    print(f"user_id: {payload['user_id']}")
    print(f"artists: {len(payload['top_artists'])}")
    print(f"genres: {len(payload['top_genres'])}")
    print(f"tracks: {len(payload['top_tracks'])}")

    # Only the four expected fields should be present.
    expected_keys = {
        "user_id",
        "top_artists",
        "top_genres",
        "top_tracks",
    }

    unexpected_keys = set(payload.keys()) - expected_keys

    if unexpected_keys:
        raise RuntimeError(
            f"Unexpected fields in payload: {sorted(unexpected_keys)}"
        )

    if payload["user_id"] == "unknown-user":
        raise RuntimeError(
            "Spotify did not return a valid user ID. Nothing was sent."
        )

    print("\nNo Spotify OAuth token or client secret is included in this payload.")

    confirmation = input(
        "\nSend this profile to the AWS API and save it to DynamoDB? (y/N): "
    ).strip().lower()

    if confirmation != "y":
        print("Cancelled. Nothing was sent to AWS.")
        return

    print(f"\nSending profile to: {save_url}")

    response = requests.post(
        save_url,
        json=payload,
        timeout=30,
    )

    print(f"\nHTTP {response.status_code}")

    try:
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
    except ValueError:
        print(response.text)

    response.raise_for_status()

    print("\nProfile was accepted by the AWS API.")

    user_id = payload["user_id"]
    profile_url = f"{api_base_url}/profiles/{user_id}"

    print("\nRetrieving the saved public profile from AWS...")

    profile_response = requests.get(
        profile_url,
        timeout=30,
    )

    print(f"\nHTTP {profile_response.status_code}")

    try:
        profile_data = profile_response.json()
        print(json.dumps(profile_data, indent=2, ensure_ascii=False))
    except ValueError:
        print(profile_response.text)

    profile_response.raise_for_status()

    print("\nSaved profile successfully retrieved from AWS.")
    print(f"user_id: {user_id}")

    print("\nNext, you can test matching with:")
    print(
        f"{api_base_url}/matches/{user_id}?limit=10"
    )


if __name__ == "__main__":
    main()