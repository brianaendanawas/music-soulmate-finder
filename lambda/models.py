from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class TasteProfile:
    user_id: str
    created_at: str
    updated_at: str
    favorite_artists: List[str]
    top_genres: List[str]
    top_tracks: List[str]
    stats: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_computed(user_id: str, computed: Dict[str, Any]) -> "TasteProfile":
        # computed is whatever your build_taste_profile returns
        favorite_artists = computed.get("favorite_artists", []) or []
        top_genres = computed.get("top_genres", []) or []
        top_tracks = computed.get("top_tracks", []) or []

        stats = computed.get("stats", {}) or {}
        artist_count = int(stats.get("artist_count", len(favorite_artists)))
        genre_variety = int(stats.get("genre_variety", len(set(top_genres))))
        track_count = int(stats.get("track_count", len(top_tracks)))

        now = iso_now()
        return TasteProfile(
            user_id=user_id,
            created_at=now,
            updated_at=now,
            favorite_artists=[str(x) for x in favorite_artists],
            top_genres=[str(x) for x in top_genres],
            top_tracks=[str(x) for x in top_tracks],
            stats={
                "artist_count": artist_count,
                "genre_variety": genre_variety,
                "track_count": track_count,
            },
        )
