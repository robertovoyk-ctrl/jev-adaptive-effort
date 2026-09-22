#!/usr/bin/env python3
"""
Convert Spotify Extended Streaming History to music_agent.py CSV format.

How to get your Spotify data:
  1. Go to spotify.com/account/privacy
  2. Request "Extended streaming history"
  3. Wait 5-30 days for the email
  4. Download the ZIP and extract it
  5. Find files named: Streaming_History_Audio_*.json

Usage:
  python spotify_import.py ~/Downloads/my_spotify_data/
  python spotify_import.py Streaming_History_Audio_2023.json

This produces library.csv ready for music_agent.py
"""

import json, csv, sys, os
from collections import Counter
from pathlib import Path

def load_spotify_files(path):
    """Load one or more Spotify JSON files."""
    path = Path(path)
    files = []

    if path.is_file() and path.suffix == ".json":
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("Streaming_History_Audio_*.json"))
        if not files:
            # Also try older format
            files = sorted(path.glob("StreamingHistory*.json"))

    if not files:
        print(f"No Spotify streaming history files found in {path}")
        print("Looking for: Streaming_History_Audio_*.json")
        sys.exit(1)

    print(f"Found {len(files)} file(s)")

    entries = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
            entries.extend(data)
            print(f"  {f.name}: {len(data)} entries")

    return entries

def convert(entries):
    """Convert Spotify entries to music_agent CSV rows."""
    rows = []
    skipped = 0

    # Count plays per track for play_count
    track_plays = Counter()
    for e in entries:
        artist = e.get("master_metadata_album_artist_name") or e.get("artistName")
        track = e.get("master_metadata_track_name") or e.get("trackName")
        if artist and track:
            track_plays[(artist, track)] += 1

    seen = set()

    for e in entries:
        # Handle both extended and basic format
        artist = e.get("master_metadata_album_artist_name") or e.get("artistName")
        track = e.get("master_metadata_track_name") or e.get("trackName")
        ts = e.get("ts") or e.get("endTime")
        ms_played = e.get("ms_played") or e.get("msPlayed") or 0

        if not artist or not track or not ts:
            skipped += 1
            continue

        # Skip very short plays (< 30 seconds = likely skipped)
        if ms_played < 30000:
            skipped += 1
            continue

        duration_sec = ms_played // 1000

        # Clean timestamp format
        timestamp = ts.replace("T", " ").replace("Z", "")
        if len(timestamp) > 19:
            timestamp = timestamp[:19]

        # Genre: Spotify doesn't include it — we mark as Unknown
        # music_agent.py handles this gracefully
        genre = "Unknown"

        rows.append({
            "timestamp": timestamp,
            "artist": artist,
            "track": track,
            "genre": genre,
            "duration_sec": duration_sec,
            "play_count": 1
        })

    return rows, skipped

def main():
    if len(sys.argv) < 2:
        print("Usage: python spotify_import.py <path-to-spotify-data>")
        print()
        print("Pass a folder containing Streaming_History_Audio_*.json files,")
        print("or a single JSON file.")
        print()
        print("Get your data: spotify.com/account/privacy → Request extended streaming history")
        sys.exit(1)

    entries = load_spotify_files(sys.argv[1])
    print(f"\nTotal entries: {len(entries)}")

    rows, skipped = convert(entries)
    rows.sort(key=lambda x: x["timestamp"])

    output = "library.csv"
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "artist", "track", "genre", "duration_sec", "play_count"])
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    artists = set(r["artist"] for r in rows)
    tracks = set((r["artist"], r["track"]) for r in rows)

    print(f"\nConverted: {len(rows)} plays")
    print(f"Skipped:   {skipped} (no metadata or < 30s)")
    print(f"Artists:   {len(artists)}")
    print(f"Tracks:    {len(tracks)}")
    if rows:
        print(f"Range:     {rows[0]['timestamp']} → {rows[-1]['timestamp']}")
    print(f"\nSaved to {output}")
    print(f"Run: python music_agent.py {output}")

if __name__ == "__main__":
    main()
