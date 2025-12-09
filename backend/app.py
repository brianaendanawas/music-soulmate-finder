from flask import Flask, jsonify, render_template

from .spotify_client import create_spotify_client
from .taste_profile import build_taste_profile


def create_app():
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
        results = sp.current_user_top_artists(limit=10)

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
        results = sp.current_user_top_tracks(limit=10)

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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
