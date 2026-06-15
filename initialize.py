#! /usr/bin/env python3

"""
Initialize player.ini with files in given directory.

Scans FILE_PATH for audio files named as "Artist-SongTitle.ext",
generates a player.ini with Song sections.
"""

import configparser
from pathlib import Path

FILE_PATH = "D:/Music"
CONFIG_FILE_PATH = "./player.ini"
DEFAULT_SONG_URL = "http://qjjlb.quanjian.com.cn/musicdl/"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}


def scan_audio_files(directory: str) -> list[dict]:
    """扫描目录下的音频文件，解析歌手和歌曲名"""
    audio_dir = Path(directory)
    if not audio_dir.is_dir():
        print(f"错误：目录不存在 - {directory}")
        return []

    songs = []
    # 收集所有音频文件
    for f in sorted(audio_dir.iterdir()):
        if f.suffix.lower() in AUDIO_EXTENSIONS:
            # 文件名格式：歌手-歌曲名.扩展名
            stem = f.stem  # 不含扩展名的文件名
            if "-" in stem:
                author, song_name = stem.split("-", 1)
                author = author.strip()
                song_name = song_name.strip()
            else:
                author = "未知"
                song_name = stem.strip()

            # 查找同名 PNG 封面
            cover_path = f.with_suffix(".png")
            cover = str(cover_path) if cover_path.is_file() else ""

            songs.append({
                "audio_file": str(f),
                "author": author,
                "song_name": song_name,
                "song_url": DEFAULT_SONG_URL,
                "cover_image": cover,
            })
            print(f"  发现歌曲：{author} - {song_name}")

    return songs


def write_config(songs: list[dict], config_path: str):
    """将歌曲信息写入 player.ini"""
    cfg = configparser.ConfigParser()
    cfg.optionxform = str  # 保留键的大小写

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

    print(f"已写入 {len(songs)} 首歌曲到 {config_path}")


def main():
    print(f"正在扫描目录：{FILE_PATH}")
    songs = scan_audio_files(FILE_PATH)

    if not songs:
        print("未找到任何音频文件，将生成空配置。")

    write_config(songs, CONFIG_FILE_PATH)
    print("完成！")


if __name__ == "__main__":
    main()