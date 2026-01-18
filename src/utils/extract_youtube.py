"""Utility to extract audio from YouTube playlists."""
import subprocess
from pathlib import Path

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLzvGATksl5N5QmQF1p0h9Np7alRJU82H5"
OUT_DIR = Path("data/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)
ITEMS_FROM = 1
ITEMS_TO = 2

cmd = [
    "yt-dlp",

    "--yes-playlist",
    "--playlist-items", f"{ITEMS_FROM}-{ITEMS_TO}",

     # Force stable extraction path
     "--js-runtimes", "node",
    "--extractor-args", "youtube:player_client=web",

    "-f", "bestaudio",
    "--extract-audio",
    "--audio-format", "wav",
    "--audio-quality", "0",

    "-o", str(OUT_DIR / "%(playlist_index)03d.%(ext)s"),

    PLAYLIST_URL,
]

subprocess.run(cmd, check=True)
