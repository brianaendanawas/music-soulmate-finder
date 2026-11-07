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

    @app.get("/my-matches")
    def get_my_matches():
        # Local development only; do not accept an arbitrary user ID from the browser.
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"error": "Local access only."}), 403

        api_base_url = os.getenv("AWS_API_BASE_URL", "").strip().rstrip("/")
        if not api_base_url.startswith("https://"):
            return jsonify({"error": "AWS_API_BASE_URL must be configured as an HTTPS URL in .env."}), 500

        try:
            sp = create_spotify_client()
            user_id = (sp.current_user() or {}).get("id")
            if not isinstance(user_id, str) or not user_id.strip():
                return jsonify({"error": "Could not identify your Spotify account."}), 401

            response = requests.get(
                f"{api_base_url}/matches/{requests.utils.quote(user_id, safe='')}",
                params={"limit": 10},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("for_user_id") != user_id or not isinstance(data.get("matches"), list):
                return jsonify({"error": "AWS returned an unexpected matches response."}), 502

            matches = [
                {
                    "user_id": match.get("user_id"),
                    "display_name": match.get("display_name"),
                    "match_percent": match.get("match_percent"),
                }
                for match in data["matches"]
                if isinstance(match, dict)
            ]
            return jsonify({"matches": matches})
        except requests.RequestException:
            app.logger.exception("AWS matches request failed")
            return jsonify({"error": "Could not retrieve AWS matches. Check the Flask terminal."}), 502
        except Exception:
            app.logger.exception("Spotify matches lookup failed")
            return jsonify({"error": "Could not load matches. Check the Flask terminal."}), 500

    @app.get("/match-profile/<user_id>")
    def get_match_profile(user_id):
        # Local development proxy for an existing AWS public profile.
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify({"error": "Local access only."}), 403

        api_base_url = os.getenv("AWS_API_BASE_URL", "").strip().rstrip("/")
        if not api_base_url.startswith("https://"):
            return jsonify({"error": "AWS_API_BASE_URL must be configured as an HTTPS URL in .env."}), 500

        if not user_id.strip() or len(user_id) > 200:
            return jsonify({"error": "Invalid user ID."}), 400

        try:
            response = requests.get(
                f"{api_base_url}/profiles/{requests.utils.quote(user_id, safe='')}",
                timeout=30,
            )
            if response.status_code == 404:
                return jsonify({"error": "Music profile not found."}), 404
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or data.get("user_id") != user_id:
                return jsonify({"error": "AWS returned an unexpected profile response."}), 502

            # Allowlist public fields only; never forward the complete AWS record.
            artists = data.get("top_artists_preview")
            genres = data.get("top_genres_preview")
            return jsonify({
                "user_id": user_id,
                "display_name": data.get("display_name") if isinstance(data.get("display_name"), str) else user_id,
                "top_artists_preview": [x for x in artists if isinstance(x, str)][:5] if isinstance(artists, list) else [],
                "top_genres_preview": [x for x in genres if isinstance(x, str)][:5] if isinstance(genres, list) else [],
            })
        except (requests.RequestException, ValueError):
            app.logger.exception("AWS public profile request failed")
            return jsonify({"error": "Could not retrieve this music profile. Check the Flask terminal."}), 502

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
