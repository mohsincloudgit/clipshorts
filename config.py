import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")

# Detect Vercel / AWS Lambda serverless environment
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

if IS_VERCEL:
    OUTPUT_DIR = Path("/tmp/output")
    BIN_DIR = Path("/tmp/bin")
else:
    OUTPUT_DIR = BASE_DIR / "output"
    BIN_DIR = BASE_DIR / "bin"

CLIPS_DIR = OUTPUT_DIR / "clips"
DOWNLOADS_DIR = OUTPUT_DIR / "downloads"
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
LOGOS_DIR = OUTPUT_DIR / "logos"
SCHEDULER_DB = OUTPUT_DIR / "scheduler.db"

# Create required directories safely (in writable /tmp on serverless)
try:
    for d in [OUTPUT_DIR, CLIPS_DIR, DOWNLOADS_DIR, TRANSCRIPTS_DIR, LOGOS_DIR, BIN_DIR]:
        d.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[Config Warning] Directory creation note: {e}")

# API Keys & Auth settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default processing settings
DEFAULT_SETTINGS = {
    "min_duration": 25,       # Min clip length in seconds
    "max_duration": 60,       # Max clip length in seconds
    "max_clips": 5,           # Number of viral clips to cut
    "reframe_mode": "blur",   # "blur", "crop", "fit"
    "caption_style": "hormozi", # "hormozi", "neon", "minimal", "none"
    "ai_provider": "gemini",  # "gemini", "groq", "openai", "auto"
    "anti_copyright": True,   # Content-ID evasion (micro tempo shift, eq, color grade)
    "logo_position": "top_right", # "top_right", "top_left", "bottom_right", "center_top"
    "logo_opacity": 0.85
}
