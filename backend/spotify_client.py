import spotipy
from spotipy.oauth2 import SpotifyOAuth

def create_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="user-top-read",
        redirect_uri="http://127.0.0.1:3000/callback"
    ))
