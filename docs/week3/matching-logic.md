# Week 3 — Matching Logic

## Goal
Compute an easy-to-explain compatibility score between two users' saved taste profiles.

## Inputs (from stored TasteProfile)
We compare:
- Top artists (from `profile.sample.top_artists`)
- Top genres (from `profile.top_genres[].genre`)
- Top tracks (from `profile.sample.top_tracks`)

All values are normalized (trimmed + lowercase) before comparison.

## Shared counts
- `shared_artists` = intersection of normalized artist sets
- `shared_genres`  = intersection of normalized genre sets
- `shared_tracks`  = intersection of normalized track sets

## Score formula
match_score = shared_artists * 3 + shared_genres * 2 + shared_tracks * 1

## Why weights?
- Artists represent strong long-term preference (highest weight)
- Genres are broad taste indicators (medium weight)
- Tracks can be more seasonal or one-off (lowest weight)

## Output
We return:
- `match_score`
- lists of shared artists/genres/tracks
- counts + weights (to explain how the score was produced)

## Example
If two users share:
- 2 artists → 2*3 = 6
- 1 genre   → 1*2 = 2
- 1 track   → 1*1 = 1

Total match_score = 9
