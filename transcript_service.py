import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from config import TRANSCRIPTS_DIR

def extract_youtube_id(url_or_id: str) -> Optional[str]:
    """Extracts YouTube 11-char video ID from various YouTube URL formats."""
    url_or_id = url_or_id.strip()
    if len(url_or_id) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', url_or_id):
        return url_or_id

    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([A-Za-z0-9_-]{11})',
        r'^([A-Za-z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def fetch_youtube_transcript(video_id: str) -> List[Dict]:
    """
    Fetches transcript directly from YouTube using youtube-transcript-api.
    Returns list of dicts with 'start', 'duration', 'text'.
    """
    cache_file = TRANSCRIPTS_DIR / f"{video_id}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()

        # Try fetching default English transcript
        try:
            t = api.fetch(video_id)
            snippets = t.snippets
        except Exception:
            # Try listing available transcripts
            try:
                t_list = api.list(video_id)
                transcript = None
                try:
                    transcript = t_list.find_transcript(['en', 'en-US', 'en-GB'])
                except Exception:
                    try:
                        transcript = t_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                    except Exception:
                        for item in t_list:
                            transcript = item.translate('en') if item.is_translatable else item
                            break
                if transcript:
                    fetched = transcript.fetch()
                    snippets = fetched.snippets if hasattr(fetched, 'snippets') else fetched
                else:
                    raise RuntimeError("No transcript found.")
            except Exception as e_inner:
                raise RuntimeError(f"Transcript lookup failed: {e_inner}")

        cleaned_data = []
        for s in snippets:
            text = getattr(s, "text", "") if hasattr(s, "text") else s.get("text", "")
            start = getattr(s, "start", 0.0) if hasattr(s, "start") else s.get("start", 0.0)
            duration = getattr(s, "duration", 2.0) if hasattr(s, "duration") else s.get("duration", 2.0)

            cleaned_data.append({
                "start": round(float(start), 2),
                "duration": round(float(duration), 2),
                "text": text.replace("\n", " ").strip()
            })

        # Cache locally
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2)

        return cleaned_data
    except Exception as e:
        print(f"[Transcript Error] Failed fetching YouTube transcript: {e}")
        return []

def format_transcript_for_ai(segments: List[Dict]) -> str:
    """Formats transcript segments with timestamps into clean readable text for AI analysis."""
    lines = []
    for item in segments:
        start_secs = item["start"]
        mins = int(start_secs // 60)
        secs = int(start_secs % 60)
        lines.append(f"[{mins:02d}:{secs:02d}] {item['text']}")
    return "\n".join(lines)
