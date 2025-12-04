from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    @app.get("/health")
    def health_check():
        """
        Simple health check endpoint.
        You can open this in the browser to confirm the backend works.
        """
        return jsonify({"status": "ok", "service": "music-soulmate-backend"})

    return app


# This block runs only when you call 'python app.py'
if __name__ == "__main__":
    app = create_app()
    # debug=True reloads on code changes (handy for development)
    app.run(debug=True)
