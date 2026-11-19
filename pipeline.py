import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import CLIPS_DIR, OUTPUT_DIR
from transcript_service import extract_youtube_id, fetch_youtube_transcript, format_transcript_for_ai
from analyzer import find_viral_moments
from downloader import get_video_info, download_youtube_video
from subtitle_service import generate_ass_subtitles
from ffmpeg_utils import cut_clip, ensure_ffmpeg
from seo_service import generate_viral_seo
from firebase_service import save_clip_to_db

def run_clip_pipeline(
    url_or_file: str,
    min_duration: int = 25,
    max_duration: int = 60,
    max_clips: int = 5,
    reframe_mode: str = "blur",
    caption_style: str = "hormozi",
    ai_provider: str = "gemini",
    api_key: str = "",
    selected_clip_indices: Optional[List[int]] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "top_right",
    logo_opacity: float = 0.85,
    anti_copyright: bool = True,
    hflip: bool = False,
    progress_callback = None
) -> Dict[str, Any]:
    """
    Executes the end-to-end viral shorts creation pipeline:
    1. Parse URL & fetch metadata
    2. Retrieve transcript
    3. AI identifies viral clips
    4. Downloads source video
    5. Cuts, reframes to 9:16 vertical, applies Anti-Copyright Shield, custom Logo, and burns subtitles
    6. Generates full Viral SEO metadata package (tags, description, clickbait title variants)
    """
    def log(step: str, pct: int):
        print(f"[{pct}%] {step}")
        if progress_callback:
            progress_callback(step, pct)

    log("Resolving video & fetching metadata...", 10)
    video_id = extract_youtube_id(url_or_file)
    if not video_id and not os.path.exists(url_or_file):
        raise ValueError("Invalid YouTube URL or local file path provided.")

    video_info = {}
    if video_id:
        try:
            video_info = get_video_info(video_id)
        except Exception as e:
            print(f"[Warning] Failed fetching info: {e}")
            video_info = {"id": video_id, "title": "YouTube Video", "uploader": "Creator", "duration": 0}
    else:
        video_id = Path(url_or_file).stem
        video_info = {"id": video_id, "title": Path(url_or_file).name, "uploader": "Local File", "duration": 0}

    log("Extracting timestamped transcript...", 25)
    segments = fetch_youtube_transcript(video_id)
    if not segments:
        raise RuntimeError("Could not retrieve captions/transcript for this video. Please ensure the video has subtitles or captions available.")

    formatted_transcript = format_transcript_for_ai(segments)

    log(f"Analyzing transcript for viral moments using {ai_provider.capitalize()}...", 45)
    viral_moments = find_viral_moments(
        transcript_text=formatted_transcript,
        segments=segments,
        min_dur=min_duration,
        max_dur=max_duration,
        max_clips=max_clips,
        preferred_provider=ai_provider,
        api_key=api_key
    )

    if not viral_moments:
        raise RuntimeError("No viral moments could be identified from the transcript.")

    # Filter to specific clips if user selected subset
    if selected_clip_indices is not None and len(selected_clip_indices) > 0:
        viral_moments = [viral_moments[i] for i in selected_clip_indices if i < len(viral_moments)]

    log("Downloading high-definition source video...", 60)
    source_video_path = download_youtube_video(video_id if video_id else url_or_file)

    shield_text = "with Anti-Copyright Shield & Logo" if anti_copyright or logo_path else ""
    log(f"Rendering 9:16 Shorts {shield_text}...", 75)
    ensure_ffmpeg()

    created_clips = []
    total_moments = len(viral_moments)

    for idx, moment in enumerate(viral_moments, start=1):
        clip_id = f"{video_id}_clip_{idx}_{uuid.uuid4().hex[:6]}"
        clip_output_path = CLIPS_DIR / f"{clip_id}.mp4"
        ass_sub_path = CLIPS_DIR / f"{clip_id}.ass"

        sub_file = None
        if caption_style != "none":
            sub_file = generate_ass_subtitles(
                transcript_segments=segments,
                clip_start=moment["start_time"],
                clip_end=moment["end_time"],
                output_ass_path=str(ass_sub_path),
                style_name=caption_style
            )

        render_ok = cut_clip(
            input_video=source_video_path,
            output_video=str(clip_output_path),
            start_time=moment["start_time"],
            end_time=moment["end_time"],
            reframe_mode=reframe_mode,
            ass_subtitle_file=sub_file,
            logo_path=logo_path,
            logo_position=logo_position,
            logo_opacity=logo_opacity,
            anti_copyright=anti_copyright,
            hflip=hflip
        )

        if render_ok and clip_output_path.exists():
            # Generate SEO package
            seo_data = generate_viral_seo(
                title=moment["title"],
                hook_text=moment["hook_text"],
                reason=moment["reason"]
            )

            clip_meta = {
                "id": clip_id,
                "file_path": str(clip_output_path),
                "filename": f"{clip_id}.mp4",
                "file_url": f"/api/clips/{clip_id}.mp4",
                "title": moment["title"],
                "start_time": moment["start_time"],
                "end_time": moment["end_time"],
                "duration": moment["duration"],
                "viral_score": moment["viral_score"],
                "hook_text": moment["hook_text"],
                "reason": moment["reason"],
                "suggested_caption": moment.get("suggested_caption", ""),
                "reframe_mode": reframe_mode,
                "caption_style": caption_style,
                "anti_copyright": anti_copyright,
                "logo_used": bool(logo_path),
                "seo": seo_data
            }
            # Save metadata alongside clip
            with open(CLIPS_DIR / f"{clip_id}.json", "w", encoding="utf-8") as f:
                json.dump(clip_meta, f, indent=2)

            # Sync to Firebase Cloud Firestore
            save_clip_to_db(clip_id, clip_meta)

            created_clips.append(clip_meta)

        pct = 75 + int((idx / total_moments) * 23)
        log(f"Processed clip {idx}/{total_moments}: '{moment['title']}'", pct)

    log("Viral Shorts generation complete!", 100)

    result = {
        "video": video_info,
        "clips": created_clips,
        "total_generated": len(created_clips)
    }

    # Save run manifest
    with open(OUTPUT_DIR / f"{video_id}_manifest.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
