from matching import compute_match_score

# Two fake profiles shaped like Day 3 output
profile_a = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 2", "NCT 127"],
        "top_tracks": ["Song A – Artist 1", "Song X – NCT 127"],
    },
    "top_genres": [{"genre": "pop", "count": 2}, {"genre": "k-pop", "count": 1}],
}

profile_b = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 3", "NCT 127"],
        "top_tracks": ["Song A – Artist 1", "Song B – Artist 3"],
    },
    "top_genres": [{"genre": "pop", "count": 1}, {"genre": "r&b", "count": 2}],
}

result = compute_match_score(profile_a, profile_b)
print(result)

"""
Expected-ish:
shared_artists: {"artist 1", "nct 127"} => 2 * 3 = 6
shared_genres: {"pop"} => 1 * 2 = 2
shared_tracks: {"song a – artist 1"} => 1 * 1 = 1
Total: 9
"""
