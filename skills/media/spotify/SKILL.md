---
name: spotify
description: "Spotify: play, search, queue, manage playlists and devices."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [spotify_playback, spotify_devices, spotify_queue, spotify_search, spotify_playlists, spotify_albums, spotify_library]
metadata:
  hermes:
    tags: [spotify, music, playback, playlists, media]
    related_skills: [gif-search, songsee, heartmula]
    trigger_conditions:
      - "play music"
      - "play X on spotify"
      - "pause"
      - "skip"
      - "queue up"
      - "what's playing"
      - "search for X on spotify"
      - "add to my playlist"
      - "create a playlist"
      - "save this song"
      - "transfer playback"
      - "volume"
      - "spotify"
---

# Spotify

Control the user's Spotify account via the Hermes Spotify toolset (7 tools). Setup guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/spotify

## When to Use

- User says "play X", "pause", "skip", "next", "previous"
- User says "queue up X" or "add to queue"
- User asks "what's playing" or "what am I listening to"
- User wants to search for and play a track, album, artist, or playlist
- User says "add to my X playlist" or "create a playlist"
- User wants to save/unsave a track or album to their library
- User says "transfer playback to my <device>"
- User wants to set volume, enable shuffle, or toggle repeat
- User asks for recently played tracks
- User says "what devices are available"

## Not For

- **Searching for or playing local audio files** → use a local media player or `songsee` for analysis
- **Music generation or AI audio creation** → use `heartmula` or `audiocraft` instead
- **Audio feature analysis (spectrograms, MFCC, chroma)** → use `songsee` instead
- **Managing Spotify account settings, billing, or profile** → use the Spotify web UI or mobile app
- **Podcast/show management** → Spotify supports some podcast ops but this skill focuses on music
- **Social features (following friends, viewing friend activity)** → use the Spotify app
- **Playing music on unsupported platforms** → this skill requires the Spotify toolset; check `hermes tools` for availability

## The 7 tools

- `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume, get_state, get_currently_playing, recently_played
- `spotify_devices` — list, transfer
- `spotify_queue` — get, add
- `spotify_search` — search the catalog
- `spotify_playlists` — list, get, create, add_items, remove_items, update_details
- `spotify_albums` — get, tracks
- `spotify_library` — list/save/remove with `kind: "tracks"|"albums"`

Playback-mutating actions require Spotify Premium; search/library/playlist ops work on Free.

## Canonical patterns (minimize tool calls)

### "Play <artist/track/album>"
One search, then play by URI. Do NOT loop through search results describing them unless the user asked for options.

```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ got album URI spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:1weenld61qoidwYuZ1GESA"})
```

For "play some <artist>" (no specific song), prefer `types: ["artist"]` and play the artist context URI — Spotify handles smart shuffle. If the user says "the song" or "that track", search `types: ["track"]` and pass `uris: [track_uri]` to play.

### "What's playing?" / "What am I listening to?"
Single call — don't chain get_state after get_currently_playing.

```
spotify_playback({"action": "get_currently_playing"})
```

If it returns 204/empty (`is_playing: false`), tell the user nothing is playing. Don't retry.

### "Pause" / "Skip" / "Volume 50"
Direct action, no preflight inspection needed.

```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

### "Add to my <playlist name> playlist"
1. `spotify_playlists list` to find the playlist ID by name
2. Get the track URI (from currently playing, or search)
3. `spotify_playlists add_items` with the playlist_id and URIs

```
spotify_playlists({"action": "list"})
→ found "Late Night Jazz" = 37i9dQZF1DX4wta20PHgwo
spotify_playback({"action": "get_currently_playing"})
→ current track uri = spotify:track:0DiWol3AO6WpXZgp0goxAV
spotify_playlists({"action": "add_items",
                   "playlist_id": "37i9dQZF1DX4wta20PHgwo",
                   "uris": ["spotify:track:0DiWol3AO6WpXZgp0goxAV"]})
```

### "Create a playlist called X and add the last 3 songs I played"
```
spotify_playback({"action": "recently_played", "limit": 3})
spotify_playlists({"action": "create", "name": "Focus 2026"})
→ got playlist_id back in response
spotify_playlists({"action": "add_items", "playlist_id": <id>, "uris": [<3 uris>]})
```

### "Save / unsave / is this saved?"
Use `spotify_library` with the right `kind`.

```
spotify_library({"kind": "tracks", "action": "save", "uris": ["spotify:track:..."]})
spotify_library({"kind": "albums", "action": "list", "limit": 50})
```

### "Transfer playback to my <device>"
```
spotify_devices({"action": "list"})
→ pick the device_id by matching name/type
spotify_devices({"action": "transfer", "device_id": "<id>", "play": true})
```

## Pitfalls

1. **Calling `get_state` before every playback action** — Spotify accepts play/pause/skip without preflight. Only call `get_currently_playing` when the user asked "what's playing" or you need to reason about the current track. Extra calls waste time and API quota.

2. **Retrying `403 No active device`** — This means Spotify isn't open on any device. Blindly retrying the same call produces the same error. Tell the user: "Open Spotify on your phone/desktop/web player first, start any track for a second, then retry." Call `spotify_devices list` to confirm the device list is empty.

3. **Describing search results when the user said "play X"** — If the user said "play Kind of Blue", search with `limit: 1`, grab the top URI, and play it. They'll hear if it's wrong. Listing every result adds friction and delay.

4. **Retrying `403 Premium required`** — This is a permanent condition for Free users on playback-mutating actions. Don't retry; inform the user. Read operations (search, playlists, library, get_state) still work on Free.

5. **Treating `204 No Content` on `get_currently_playing` as an error** — It means nothing is currently playing. The response includes `is_playing: false`. Report that to the user without retrying or escalating.

6. **Searching `spotify_search` to find a user playlist by name** — `spotify_search` queries the public Spotify catalog. User-created playlists come from `spotify_playlists list`. If you search for "My Workout Mix" via `spotify_search`, you won't find it.

7. **Mixing `kind: "tracks"` with album URIs in `spotify_library`** — The tool normalizes IDs internally, but the API endpoint differs. Pass track URIs for `kind: "tracks"` and album URIs for `kind: "albums"`.

8. **Looping on `429 Too Many Requests`** — Rate limits mean you're calling too fast. Wait a few seconds and retry once. If it happens again, you're in a loop — stop and inform the user.

9. **Ignoring `401 Unauthorized` after retry** — This means the refresh token was revoked (user changed password, revoked app access, etc.). Tell the user to run `hermes auth spotify` again. No amount of retrying fixes this.

10. **Forgetting the `play: true` flag on device transfer** — `spotify_devices({"action": "transfer", "device_id": "..."})` without `play: true` transfers but doesn't start playback. The user will see the device active but nothing playing.

11. **Using bare IDs instead of full URIs** — While the tools accept bare IDs, full URIs (`spotify:track:...`) are unambiguous. Pass the `uri` field directly from search results to avoid entity-type mismatches.

12. **Creating duplicate playlists** — `spotify_playlists({"action": "create", "name": "X"})` always creates a new playlist. If the user said "add to my Focus playlist", first call `spotify_playlists list` to find the existing ID, then `add_items`.

## URI and ID formats

Spotify uses three interchangeable ID formats. The tools accept all three and normalize:

- URI: `spotify:track:0DiWol3AO6WpXZgp0goxAV` (preferred)
- URL: `https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV`
- Bare ID: `0DiWol3AO6WpXZgp0goxAV`

When in doubt, use full URIs. Search results return URIs in the `uri` field — pass those directly.

Entity types: `track`, `album`, `artist`, `playlist`, `show`, `episode`. Use the right type for the action — `spotify_playback.play` with a `context_uri` expects album/playlist/artist; `uris` expects an array of track URIs.
