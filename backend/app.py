import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from .taste_profile import collect_spotify_profile_data

from .spotify_client import create_spotify_client
from .taste_profile import build_taste_profile


def create_app():
    load_dotenv()
    app = Flask(__name__)

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok", "service": "music-soulmate-backend"})

    @app.get("/me")
    def get_me():
        sp = create_spotify_client()
        user = sp.current_user()

        images = user.get("images") or []
        image_url = images[0]["url"] if images else None

        profile = {
            "id": user.get("id"),
            "display_name": user.get("display_name"),
            "spotify_url": user.get("external_urls", {}).get("spotify"),
            "image_url": image_url,
            "followers": user.get("followers", {}).get("total"),
        }

        return jsonify({"profile": profile})

    @app.get("/top-artists")
    def get_top_artists():
        sp = create_spotify_client()
        results = sp.current_user_top_artists(
            limit=10,
            time_range="short_term"  # last ~4 weeks
        )

        artists = []
        for a in results["items"]:
            images = a.get("images") or []
            image_url = images[0]["url"] if images else None

            artists.append(
                {
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "image_url": image_url,
                    "genres": a.get("genres") or [],
                }
            )

        return jsonify({"top_artists": artists})

    @app.get("/top-tracks")
    def get_top_tracks():
        sp = create_spotify_client()
        results = sp.current_user_top_tracks(
            limit=10,
            time_range="short_term"
        )

        tracks = [
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "artists": [artist["name"] for artist in t.get("artists", [])],
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "preview_url": t.get("preview_url"),
            }
            for t in results["items"]
        ]

        return jsonify({"top_tracks": tracks})

    @app.get("/taste-profile")
    def get_taste_profile():
        sp = create_spotify_client()
        taste_profile = build_taste_profile(sp)
        return jsonify({"taste_profile": taste_profile})

    @app.post("/sync-profile")
    def sync_profile():
        # This endpoint is for the local development dashboard only.
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"error": "Local access only."}), 403

        api_base_url = os.getenv("AWS_API_BASE_URL", "").strip().rstrip("/")
        if not api_base_url or not api_base_url.startswith("https://"):
            return jsonify({"error": "AWS_API_BASE_URL must be configured as an HTTPS URL in .env."}), 500

        try:
            sp = create_spotify_client()
            payload = collect_spotify_profile_data(sp)
            expected_keys = {"user_id", "top_artists", "top_genres", "top_tracks"}
            if set(payload) != expected_keys or not isinstance(payload["user_id"], str) or not payload["user_id"].strip() or payload["user_id"] == "unknown-user" or any(not isinstance(payload[key], list) for key in ("top_artists", "top_genres", "top_tracks")):
                return jsonify({"error": "Invalid Spotify profile payload. Nothing was sent."}), 400

            response = requests.post(
                f"{api_base_url}/taste-profile", json=payload, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            if result.get("user_id") != payload["user_id"]:
                return jsonify({"error": "AWS returned an unexpected user ID."}), 502
            return jsonify({"message": "Profile saved to AWS", "user_id": payload["user_id"], "aws_status": response.status_code})
        except requests.RequestException:
            app.logger.exception("AWS profile sync request failed")
            return jsonify({"error": "Could not save profile to AWS. Check the Flask terminal."}), 502
        except Exception:
            app.logger.exception("Spotify profile sync failed")
            return jsonify({"error": "Profile sync failed. Check the Flask terminal."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
