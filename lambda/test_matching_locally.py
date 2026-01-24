from matching import compute_match_score

# Day 3 shape (sample + ranked genres dicts)
profile_a_day3 = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 2", "NCT 127"],
        "top_tracks": ["Song A – Artist 1", "Song X – NCT 127"],
    },
    "top_genres": [{"genre": "pop", "count": 2}, {"genre": "k-pop", "count": 1}],
}

profile_b_day3 = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 3", "NCT 127"],
        "top_tracks": ["Song A – Artist 1", "Song B – Artist 3"],
    },
    "top_genres": [{"genre": "pop", "count": 1}, {"genre": "r&b", "count": 2}],
}

# "Preview"/older-ish shape (what your public profile tends to expose)
profile_c_preview = {
    "top_artists_preview": ["NCT 127", "The Weeknd", "SZA"],
    "top_genres_preview": ["k-pop", "pop"],
    "top_tracks": ["Song A – Artist 1"],  # alternate key path
}

profile_d_preview = {
    "top_artists": ["NCT 127", "Taylor Swift"],  # alternate key path
    "top_genres": ["pop", "k-pop"],              # strings not dicts
    "sample": {"top_tracks": ["Song A – Artist 1"]},
}

print("=== Day 3 vs Day 3 ===")
print(compute_match_score(profile_a_day3, profile_b_day3))

print("\n=== Preview vs Preview ===")
print(compute_match_score(profile_c_preview, profile_d_preview))
