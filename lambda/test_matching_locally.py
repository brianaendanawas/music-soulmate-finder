from matching import compute_match_score

# Day 3 shape (sample + ranked genres dicts)
profile_a_day3 = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 2", "NCT 127"],
        "top_tracks": ["Song A \u2013 Artist 1", "Song X \u2013 NCT 127"],  # \u2013 en dash
    },
    "top_genres": [{"genre": "pop", "count": 2}, {"genre": "k-pop", "count": 1}],
}

profile_b_day3 = {
    "sample": {
        "top_artists": ["Artist 1", "Artist 3", "NCT 127"],
        "top_tracks": ["Song A \u2013 Artist 1", "Song B \u2013 Artist 3"],  # \u2013 en dash
    },
    "top_genres": [{"genre": "pop", "count": 1}, {"genre": "r&b", "count": 2}],
}

# "Preview"/older-ish shape (what your public profile tends to expose)
profile_c_preview = {
    "top_artists_preview": ["NCT 127", "The Weeknd", "SZA"],
    "top_genres_preview": ["k-pop", "pop"],
    "top_tracks": ["Song A \u2013 Artist 1"],  # \u2013 en dash
}

profile_d_preview = {
    "top_artists": ["NCT 127", "Taylor Swift"],
    "top_genres": ["pop", "k-pop"],
    "sample": {"top_tracks": ["Song A \u2013 Artist 1"]},  # \u2013 en dash
}

# Big-overlap test to prove capping works (raw > 100 -> match_score = 100)
profile_big_a = {
    "top_artists_preview": [f"Artist {i}" for i in range(1, 31)],   # 30
    "top_genres_preview": [f"Genre {i}" for i in range(1, 21)],     # 20
    "top_tracks": [f"Song {i} \u2013 Artist {i}" for i in range(1, 31)],  # en dash
}
profile_big_b = {
    "top_artists_preview": [f"Artist {i}" for i in range(1, 31)],
    "top_genres_preview": [f"Genre {i}" for i in range(1, 21)],
    "top_tracks": [f"Song {i} \u2013 Artist {i}" for i in range(1, 31)],
}

def show_tracks(label: str, res: dict) -> None:
    # Show repr() so we can see the *actual* characters (dash vs hyphen)
    print(label)
    print("shared_tracks:", res["shared_tracks"])
    print("shared_tracks repr:", [repr(x) for x in res["shared_tracks"]])

print("=== Day 3 vs Day 3 ===")
print(compute_match_score(profile_a_day3, profile_b_day3))

print("\n=== Preview vs Preview ===")
print(compute_match_score(profile_c_preview, profile_d_preview))

print("\n=== Big overlap (cap test) ===")
res = compute_match_score(profile_big_a, profile_big_b)
print(res)
print(f'raw_score={res["raw_score"]}  match_score={res["match_score"]}  match_percent={res["match_percent"]}')

# -----------------------
# Day 2 Proof Test #1: Dash normalization
# Make the dash types explicit:
#   A uses en dash \u2013
#   B uses ASCII hyphen-minus \u002d
# -----------------------
profile_dash_a = {"sample": {"top_tracks": ["Song A \u2013 Artist 1"]}}  # en dash
profile_dash_b = {"sample": {"top_tracks": ["Song A \u002d Artist 1"]}}  # hyphen

print("\n=== Day 2 Proof #1: Dash normalization (\\u2013 vs \\u002d) ===")
res_dash = compute_match_score(profile_dash_a, profile_dash_b)
print(res_dash)
show_tracks("Dash proof details:", res_dash)
assert res_dash["counts"]["tracks"] == 1, "Expected 1 shared track after dash normalization"

# -----------------------
# Day 2 Proof Test #2: feat/ft normalization
# Make everything explicit:
#   - feat. vs ft
#   - en dash vs ASCII hyphen
# -----------------------
profile_feat_a = {"sample": {"top_tracks": ["Song Z (feat. X) \u2013 Artist 9"]}}  # en dash
profile_feat_b = {"sample": {"top_tracks": ["Song Z (ft X) \u002d Artist 9"]}}     # hyphen

print("\n=== Day 2 Proof #2: feat/ft normalization (feat. vs ft) ===")
res_feat = compute_match_score(profile_feat_a, profile_feat_b)
print(res_feat)
show_tracks("Feat proof details:", res_feat)
assert res_feat["counts"]["tracks"] == 1, "Expected 1 shared track after feat/ft normalization"

print("\n✅ All Day 2 normalization tests passed.")
