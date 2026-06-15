#! /usr/bin/env python3

"""
Initialize player.ini with files in given directory.

Scans FILE_PATH for audio files named as "Artist-SongTitle.ext",
generates a player.ini with Song sections.
"""

import configparser
from pathlib import Path

FILE_PATH = "./data/song"
CONFIG_FILE_PATH = "./player.ini"
DEFAULT_SONG_URL = "http://qjjlb.quanjian.com.cn/musicdl/"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}


def scan_audio_files(directory: str) -> list[dict]:
    """Scan the given directory for audio files and extract song info."""
    audio_dir = Path(directory)
    if not audio_dir.is_dir():
        print(f"Error：Directory does not exist - {directory}")
        return []

    songs = []
    # Collect audio files and their info
    for f in sorted(audio_dir.iterdir()):
        if f.suffix.lower() in AUDIO_EXTENSIONS:
            # File name format: "Artist-SongTitle.ext"
            stem = f.stem  # Get file name without extension
            if "-" in stem:
                author, song_name = stem.split("-", 1)
                author = author.strip()
                song_name = song_name.strip()
            else:
                author = "Unknown Artist"
                song_name = stem.strip()

            # Search for cover image with the same name but .png extension
            cover_path = f.with_suffix(".png")
            cover = str(cover_path) if cover_path.is_file() else ""

            songs.append({
                "audio_file": str(f),
                "author": author,
                "song_name": song_name,
                "song_url": DEFAULT_SONG_URL,
                "cover_image": cover,
            })
            print(f"  Found song: {author} - {song_name}")

    return songs


def write_config(songs: list[dict], config_path: str):
    """Write song info to player.ini"""
    cfg = configparser.ConfigParser()
    cfg.optionxform = str  # Preserve case sensitivity for keys

    for i, song in enumerate(songs, start=1):
        section = f"Song #{i}"
        cfg[section] = {
            "audio_file": song["audio_file"],
            "author": song["author"],
            "song_name": song["song_name"],
            "song_url": song["song_url"],
            "cover_image": song["cover_image"],
        }

    with open(config_path, "w", encoding="utf-8") as f:
        cfg.write(f)

    print(f"Successfully written {len(songs)} songs to {config_path}")


def main():
    print(f"Scanning directory: {FILE_PATH}")
    songs = scan_audio_files(FILE_PATH)

    if not songs:
        print("No audio files found, generating empty config.")

    write_config(songs, CONFIG_FILE_PATH)
    print("Done!")


if __name__ == "__main__":
    main()