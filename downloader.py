import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional
from config import DOWNLOADS_DIR
from ffmpeg_utils import get_ffmpeg_path

def get_video_info(url_or_id: str) -> Dict[str, Any]:
    """Retrieves metadata for a YouTube video without downloading it."""
    import yt_dlp

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    url = url_or_id if url_or_id.startswith("http") else f"https://www.youtube.com/watch?v={url_or_id}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader", "Unknown Channel"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "view_count": info.get("view_count", 0),
            "url": url
        }

def download_youtube_video(url_or_id: str, max_height: int = 1080, progress_callback = None) -> str:
    """
    Downloads YouTube video to DOWNLOADS_DIR/{video_id}.mp4.
    If already downloaded, returns the cached file path immediately.
    """
    import yt_dlp

    url = url_or_id if url_or_id.startswith("http") else f"https://www.youtube.com/watch?v={url_or_id}"
    
    # Extract ID
    info_opts = {'skip_download': True, 'quiet': True}
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_id = info.get("id")

    target_path = DOWNLOADS_DIR / f"{video_id}.mp4"
    if target_path.exists() and target_path.stat().st_size > 1024 * 1024:
        print(f"[Downloader] Using existing cached video: {target_path}")
        return str(target_path)

    ffmpeg_path = get_ffmpeg_path()
    ffmpeg_dir = str(Path(ffmpeg_path).parent) if ffmpeg_path else None

    ydl_opts = {
        'format': f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]/best',
        'outtmpl': str(DOWNLOADS_DIR / f"{video_id}.%(ext)s"),
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    if progress_callback:
        def hook(d):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    progress_callback(float(p))
                except Exception:
                    pass
        ydl_opts['progress_hooks'] = [hook]

    print(f"[Downloader] Downloading YouTube video {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the resulting file
    for ext in ['mp4', 'mkv', 'webm']:
        cand = DOWNLOADS_DIR / f"{video_id}.{ext}"
        if cand.exists():
            return str(cand)

    return str(target_path)

