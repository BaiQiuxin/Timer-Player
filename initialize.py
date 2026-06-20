#! /usr/bin/env python3

"""
Initialize player.ini with FLAC files in given directory.

Scans FILE_PATH for .flac files, reads metadata tags (ARTIST, TITLE)
and embedded cover art via mutagen, extracts cover to ./data/album,
and generates player.ini with Song sections.
"""

import configparser
from pathlib import Path
from mutagen.flac import FLAC

FILE_PATH = "./data/song"
ALBUM_PATH = "./data/album"
CONFIG_FILE_PATH = "./player.ini"
DEFAULT_SONG_URL = "https://www.youtube.com"
AUDIO_EXTENSIONS = {".flac"}


def extract_cover(flac_file: Path, album_dir: Path) -> str:
    """
    Extract embedded cover art from FLAC and save as PNG in album_dir.
    Returns the path to the saved cover image, or empty string on failure.
    """
    try:
        audio = FLAC(str(flac_file))
        if not audio.pictures:
            return ""

        picture = audio.pictures[0]
        img_data = picture.data

        # Determine output filename (always .png)
        out_path = album_dir / (flac_file.stem + ".png")

        # If the embedded image is already PNG, write directly;
        # otherwise let Pillow convert it
        if picture.mime == "image/png":
            out_path.write_bytes(img_data)
        else:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_data))
            img.save(out_path, "PNG")

        return str(out_path)
    except Exception as e:
        print(f"  Warning: Failed to extract cover from {flac_file.name}: {e}")
        return ""


def scan_audio_files(directory: str) -> list[dict]:
    """
    Scan the given directory for .flac files and extract song info
    from metadata tags and embedded cover art.
    """
    audio_dir = Path(directory)
    if not audio_dir.is_dir():
        print(f"Error：Directory does not exist - {directory}")
        return []

    album_dir = Path(ALBUM_PATH)
    album_dir.mkdir(parents=True, exist_ok=True)

    songs = []
    for f in sorted(audio_dir.iterdir()):
        if f.suffix.lower() in AUDIO_EXTENSIONS:
            try:
                audio = FLAC(str(f))
            except Exception as e:
                print(f"  Warning: Cannot read {f.name}: {e}")
                continue

            # Read ARTIST and TITLE from FLAC tags
            author = audio.get("ARTIST", ["Unknown Artist"])[0]
            song_name = audio.get("TITLE", [f.stem])[0]

            # Extract embedded cover art
            cover = extract_cover(f, album_dir)

            songs.append({
                "audio_file": str(f),
                "author": author,
                "song_name": song_name,
                "song_url": DEFAULT_SONG_URL,
                "cover_image": cover,
            })
            print(f"  Found song: {author} - {song_name}")

    return songs


def load_existing_urls(config_path: str) -> dict[str, str]:
    """Load existing config and return a dict mapping audio_file → song_url."""
    existing = {}
    if not Path(config_path).is_file():
        return existing
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    for section in cfg.sections():
        if section.startswith("Song"):
            af = cfg[section].get("audio_file", "")
            url = cfg[section].get("song_url", "")
            if af:
                existing[af] = url
    return existing


def write_config(songs: list[dict], config_path: str):
    """Write song info to player.ini, preserving custom song URLs."""
    existing_urls = load_existing_urls(config_path)

    cfg = configparser.ConfigParser()
    cfg.optionxform = str  # Preserve case sensitivity for keys

    for i, song in enumerate(songs, start=1):
        section = f"Song #{i}"

        # Preserve custom song URL if it differs from the default
        song_url = song["song_url"]
        old_url = existing_urls.get(song["audio_file"])
        if old_url is not None and old_url != DEFAULT_SONG_URL:
            song_url = old_url
            print(f"  Preserved custom URL for: {song['author']} - {song['song_name']}")

        cfg[section] = {
            "audio_file": song["audio_file"],
            "author": song["author"],
            "song_name": song["song_name"],
            "song_url": song_url,
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