import os
import json
import uuid
import threading
import time
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import CLIPS_DIR, OUTPUT_DIR, LOGOS_DIR, GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, IS_VERCEL
from transcript_service import extract_youtube_id, fetch_youtube_transcript, format_transcript_for_ai
from analyzer import find_viral_moments
from downloader import get_video_info, download_youtube_video
from subtitle_service import generate_ass_subtitles
from ffmpeg_utils import cut_clip, get_ffmpeg_path, ensure_ffmpeg
from seo_service import generate_viral_seo
from publisher_service import (
    schedule_post,
    get_scheduled_posts,
    delete_scheduled_post,
    process_due_posts,
    get_social_config,
    save_social_config
)
from firebase_service import (
    init_firebase,
    is_firebase_active,
    save_clip_to_db,
    get_clips_from_db,
    save_scheduled_post_to_db,
    get_scheduled_posts_from_db,
    delete_scheduled_post_from_db
)

# Auto-initialize Firebase if credentials exist
init_firebase()

app = FastAPI(title="ViralShorts Studio Pro - AI YouTube to Viral Shorts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active processing jobs
jobs_status = {}

# Background scheduler loop
def scheduler_worker():
    while True:
        try:
            due_results = process_due_posts()
            if due_results:
                print(f"[Scheduler Worker] Published {len(due_results)} due posts!")
        except Exception as e:
            print(f"[Scheduler Worker Error] {e}")
        time.sleep(30)

# Start background scheduler thread only in persistent server mode (not serverless)
if not IS_VERCEL:
    threading.Thread(target=scheduler_worker, daemon=True).start()

class AnalyzeRequest(BaseModel):
    url: str
    min_duration: int = 25
    max_duration: int = 60
    max_clips: int = 5
    ai_provider: str = "gemini"
    api_key: Optional[str] = ""

class RenderRequest(BaseModel):
    url: str
    clip: dict
    reframe_mode: str = "blur"
    caption_style: str = "hormozi"
    logo_path: Optional[str] = None
    logo_position: str = "top_right"
    logo_opacity: float = 0.85
    anti_copyright: bool = True
    hflip: bool = False

class AutoCreateRequest(BaseModel):
    url: str
    min_duration: int = 25
    max_duration: int = 60
    max_clips: int = 4
    reframe_mode: str = "blur"
    caption_style: str = "hormozi"
    ai_provider: str = "gemini"
    api_key: Optional[str] = ""
    logo_path: Optional[str] = None
    logo_position: str = "top_right"
    logo_opacity: float = 0.85
    anti_copyright: bool = True
    hflip: bool = False

class ScheduleRequest(BaseModel):
    clip_id: str
    title: str
    description: str
    tags: str
    platforms: List[str]
    scheduled_time: str

@app.get("/api/system")
def get_system_status():
    ffmpeg_ready = bool(get_ffmpeg_path())
    return {
        "ffmpeg_ready": ffmpeg_ready,
        "ffmpeg_path": get_ffmpeg_path(),
        "has_gemini_key": bool(GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")),
        "has_groq_key": bool(GROQ_API_KEY or os.getenv("GROQ_API_KEY")),
        "has_openai_key": bool(OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")),
        "firebase_active": is_firebase_active(),
    }

# 1. Custom Logo Upload
@app.post("/api/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, or WebP logo images are supported.")

    file_id = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    dest_path = LOGOS_DIR / file_id

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    return {
        "filename": file_id,
        "path": str(dest_path),
        "url": f"/api/logos/{file_id}"
    }

@app.get("/api/logos")
def list_logos():
    logos = []
    for f in LOGOS_DIR.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            logos.append({
                "filename": f.name,
                "path": str(f),
                "url": f"/api/logos/{f.name}"
            })
    return logos

@app.get("/api/logos/{filename}")
def get_logo(filename: str):
    p = LOGOS_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Logo not found")
    return FileResponse(p)

# 2. Viral SEO Generator
@app.post("/api/generate-seo")
def generate_seo_endpoint(req: dict):
    title = req.get("title", "Viral Short")
    hook = req.get("hook_text", "")
    reason = req.get("reason", "")
    return generate_viral_seo(title, hook, reason)

# 3. Analyze Video
@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    video_id = extract_youtube_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        info = get_video_info(video_id)
    except Exception:
        info = {"id": video_id, "title": "YouTube Video", "uploader": "Creator", "duration": 0}

    segments = fetch_youtube_transcript(video_id)
    if not segments:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve English subtitles/transcript for this video. Please choose a video with captions."
        )

    formatted = format_transcript_for_ai(segments)
    viral_moments = find_viral_moments(
        transcript_text=formatted,
        segments=segments,
        min_dur=req.min_duration,
        max_dur=req.max_duration,
        max_clips=req.max_clips,
        preferred_provider=req.ai_provider,
        api_key=req.api_key or ""
    )

    # Attach SEO preview to each moment
    for m in viral_moments:
        m["seo"] = generate_viral_seo(m["title"], m.get("hook_text", ""), m.get("reason", ""))

    return {
        "video": info,
        "moments": viral_moments,
        "transcript_count": len(segments)
    }

# 4. Render Single Clip
@app.post("/api/render-clip")
def render_single_clip(req: RenderRequest):
    video_id = extract_youtube_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    moment = req.clip
    ensure_ffmpeg()

    # Download source video
    video_path = download_youtube_video(video_id)

    # Subtitles
    segments = fetch_youtube_transcript(video_id)
    clip_id = f"{video_id}_clip_{uuid.uuid4().hex[:6]}"
    clip_output_path = CLIPS_DIR / f"{clip_id}.mp4"
    ass_sub_path = CLIPS_DIR / f"{clip_id}.ass"

    sub_file = None
    if req.caption_style != "none" and segments:
        sub_file = generate_ass_subtitles(
            transcript_segments=segments,
            clip_start=moment["start_time"],
            clip_end=moment["end_time"],
            output_ass_path=str(ass_sub_path),
            style_name=req.caption_style
        )

    ok = cut_clip(
        input_video=video_path,
        output_video=str(clip_output_path),
        start_time=moment["start_time"],
        end_time=moment["end_time"],
        reframe_mode=req.reframe_mode,
        ass_subtitle_file=sub_file,
        logo_path=req.logo_path,
        logo_position=req.logo_position,
        logo_opacity=req.logo_opacity,
        anti_copyright=req.anti_copyright,
        hflip=req.hflip
    )

    if not ok or not clip_output_path.exists():
        raise HTTPException(status_code=500, detail="FFmpeg failed to render the short clip.")

    seo_data = generate_viral_seo(
        title=moment.get("title", "Viral Short"),
        hook_text=moment.get("hook_text", ""),
        reason=moment.get("reason", "")
    )

    meta = {
        "id": clip_id,
        "filename": f"{clip_id}.mp4",
        "file_path": str(clip_output_path),
        "file_url": f"/api/clips/{clip_id}.mp4",
        "title": moment.get("title", "Viral Short"),
        "start_time": moment.get("start_time"),
        "end_time": moment.get("end_time"),
        "duration": moment.get("duration", round(moment["end_time"] - moment["start_time"], 1)),
        "viral_score": moment.get("viral_score", 90),
        "hook_text": moment.get("hook_text", ""),
        "reason": moment.get("reason", ""),
        "suggested_caption": moment.get("suggested_caption", ""),
        "reframe_mode": req.reframe_mode,
        "caption_style": req.caption_style,
        "anti_copyright": req.anti_copyright,
        "logo_used": bool(req.logo_path),
        "seo": seo_data
    }

    with open(CLIPS_DIR / f"{clip_id}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta

# 5. Batch Auto-Create Job
@app.post("/api/create-all")
def create_all_job(req: AutoCreateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs_status[job_id] = {
        "status": "processing",
        "step": "Starting analysis...",
        "progress": 5,
        "clips": [],
        "error": None
    }

    def run_job():
        from pipeline import run_clip_pipeline
        try:
            def on_progress(step, pct):
                jobs_status[job_id]["step"] = step
                jobs_status[job_id]["progress"] = pct

            res = run_clip_pipeline(
                url_or_file=req.url,
                min_duration=req.min_duration,
                max_duration=req.max_duration,
                max_clips=req.max_clips,
                reframe_mode=req.reframe_mode,
                caption_style=req.caption_style,
                ai_provider=req.ai_provider,
                api_key=req.api_key or "",
                logo_path=req.logo_path,
                logo_position=req.logo_position,
                logo_opacity=req.logo_opacity,
                anti_copyright=req.anti_copyright,
                hflip=req.hflip,
                progress_callback=on_progress
            )
            for c in res["clips"]:
                c["file_url"] = f"/api/clips/{c['filename']}"

            jobs_status[job_id]["status"] = "completed"
            jobs_status[job_id]["progress"] = 100
            jobs_status[job_id]["step"] = "Finished!"
            jobs_status[job_id]["clips"] = res["clips"]
            jobs_status[job_id]["video"] = res["video"]
        except Exception as e:
            jobs_status[job_id]["status"] = "failed"
            jobs_status[job_id]["error"] = str(e)

    background_tasks.add_task(run_job)
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_status[job_id]

# 6. Clips Listing & Streaming
@app.get("/api/clips")
def list_clips():
    clips = []
    for meta_file in CLIPS_DIR.glob("*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["file_url"] = f"/api/clips/{data.get('filename', '')}"
                clips.append(data)
        except Exception:
            pass
    clips.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
    return clips

@app.get("/api/clips/{filename}")
def stream_clip(filename: str):
    file_path = CLIPS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type="video/mp4")

# 7. Post Scheduling Endpoints
@app.post("/api/schedule")
def schedule_post_endpoint(req: ScheduleRequest):
    # Find clip path
    clip_path = str(CLIPS_DIR / f"{req.clip_id}.mp4")
    if not os.path.exists(clip_path):
        # Check by filename
        candidates = list(CLIPS_DIR.glob(f"*{req.clip_id}*.mp4"))
        if candidates:
            clip_path = str(candidates[0])
        else:
            raise HTTPException(status_code=404, detail="Clip video file not found")

    post_id = schedule_post(
        clip_id=req.clip_id,
        clip_path=clip_path,
        title=req.title,
        description=req.description,
        tags=req.tags,
        platforms=req.platforms,
        scheduled_time=req.scheduled_time
    )
    return {"success": True, "post_id": post_id}

@app.get("/api/scheduled-posts")
def get_scheduled_posts_endpoint():
    return get_scheduled_posts()

@app.delete("/api/delete-scheduled/{post_id}")
def delete_scheduled_endpoint(post_id: int):
    ok = delete_scheduled_post(post_id)
    return {"success": ok}

# 8. Social Media Credentials & Configuration
@app.get("/api/social-config")
def get_social_config_endpoint():
    return get_social_config()

@app.post("/api/social-config")
def save_social_config_endpoint(req: dict):
    ok = save_social_config(req)
    return {"success": ok}

@app.post("/api/upload-youtube-secrets")
async def upload_youtube_secrets(file: UploadFile = File(...)):
    dest = Path("client_secrets.json")
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    # Update config
    cfg = get_social_config()
    cfg["youtube"]["client_secrets"] = str(dest.resolve())
    cfg["youtube"]["enabled"] = True
    save_social_config(cfg)
    return {"success": True, "path": str(dest.resolve())}

@app.post("/api/upload-firebase-credentials")
async def upload_firebase_credentials(file: UploadFile = File(...)):
    dest = Path("serviceAccountKey.json")
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    # Re-initialize Firebase
    ok = init_firebase()
    return {"success": ok, "path": str(dest.resolve()), "firebase_connected": is_firebase_active()}

# 9. Web UI
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>ViralShorts Studio Pro Backend Active</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=True)
