import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional
from config import BIN_DIR

def get_ffmpeg_path() -> str:
    """Finds ffmpeg executable in system PATH, local bin, or known locations."""
    local_bin = BIN_DIR / "ffmpeg.exe"
    if local_bin.exists():
        return str(local_bin)

    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    common_paths = [
        Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        Path(os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg\bin\ffmpeg.exe")),
    ]
    for p in common_paths:
        if p.exists():
            return str(p)

    return ""

def get_ffprobe_path() -> str:
    """Finds ffprobe executable."""
    local_bin = BIN_DIR / "ffprobe.exe"
    if local_bin.exists():
        return str(local_bin)
    sys_probe = shutil.which("ffprobe")
    if sys_probe:
        return sys_probe
    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        probe_candidate = Path(ffmpeg).parent / "ffprobe.exe"
        if probe_candidate.exists():
            return str(probe_candidate)
    return ""

def ensure_ffmpeg() -> str:
    """Ensures ffmpeg is available, downloading a portable build if missing."""
    path = get_ffmpeg_path()
    if path:
        return path

    print("[FFmpeg] FFmpeg not found on system. Installing portable FFmpeg for Windows...")
    zip_url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    zip_dest = BIN_DIR / "ffmpeg.zip"

    try:
        print(f"[FFmpeg] Downloading static binary package...")
        urllib.request.urlretrieve(zip_url, zip_dest)
        print("[FFmpeg] Extracting ffmpeg.exe and ffprobe.exe...")
        with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if filename in ["ffmpeg.exe", "ffprobe.exe"]:
                    with zip_ref.open(member) as source, open(BIN_DIR / filename, "wb") as target:
                        shutil.copyfileobj(source, target)
        if zip_dest.exists():
            zip_dest.unlink()
        print(f"[FFmpeg] Installed successfully to {BIN_DIR}")
        return str(BIN_DIR / "ffmpeg.exe")
    except Exception as e:
        print(f"[FFmpeg] Download failed: {e}. Please install ffmpeg or run: winget install Gyan.FFmpeg")
        return ""

def cut_clip(
    input_video: str,
    output_video: str,
    start_time: float,
    end_time: float,
    reframe_mode: str = "blur",
    ass_subtitle_file: Optional[str] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "top_right",
    logo_opacity: float = 0.85,
    anti_copyright: bool = True,
    hflip: bool = False
) -> bool:
    """
    Cuts and reframes a video segment into a 9:16 vertical Short (1080x1920).
    Features:
      - 9:16 vertical reframe (blur, crop, or fit)
      - Anti-Copyright Shield (micro tempo/pitch shift, color grading to bypass Content-ID)
      - Custom Logo/Watermark overlay with opacity and positioning
      - Dynamic animated burned subtitles
    """
    ffmpeg_exe = ensure_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg executable could not be found or downloaded.")

    duration = max(1.0, end_time - start_time)

    filter_chains = []

    # 1. Base Reframe
    if reframe_mode == "blur":
        filter_chains.append(
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];"
            "[0:v]scale=1080:-1[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[basev]"
        )
    elif reframe_mode == "crop":
        filter_chains.append(
            "[0:v]crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920[basev]"
        )
    else: # "fit"
        filter_chains.append(
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(1080-iw)/2:(1920-ih)/2:black[basev]"
        )

    current_v = "[basev]"

    # 2. Anti-Copyright Shield Video Filters
    if anti_copyright:
        shield_filters = ["eq=contrast=1.04:brightness=0.01:saturation=1.06"]
        if hflip:
            shield_filters.append("hflip")
        filter_chains.append(f"{current_v}{','.join(shield_filters)}[shieldv]")
        current_v = "[shieldv]"

    # 3. Logo Overlay
    inputs = ["-i", input_video]
    if logo_path and os.path.exists(logo_path):
        inputs.extend(["-i", logo_path])
        pos_map = {
            "top_right": "W-w-40:60",
            "top_left": "40:60",
            "bottom_right": "W-w-40:H-h-240",
            "bottom_left": "40:H-h-240",
            "center_top": "(W-w)/2:60"
        }
        pos_expr = pos_map.get(logo_position, "W-w-40:60")
        filter_chains.append(
            f"[1:v]scale=180:-1,format=rgba,colorchannelmixer=aa={logo_opacity}[logo];"
            f"{current_v}[logo]overlay={pos_expr}[logov]"
        )
        current_v = "[logov]"

    # 4. Burn Dynamic Subtitles
    if ass_subtitle_file and os.path.exists(ass_subtitle_file):
        safe_sub_path = ass_subtitle_file.replace("\\", "/").replace(":", "\\:")
        filter_chains.append(f"{current_v}ass='{safe_sub_path}'[subv]")
        current_v = "[subv]"

    final_filter_complex = ";".join(filter_chains)

    # 5. Audio Filtering (Anti-Copyright Shield Audio Modulation)
    audio_filters = []
    if anti_copyright:
        audio_filters.append("atempo=1.025,equalizer=f=1200:t=q:w=1.2:g=1.2")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        *inputs,
        "-filter_complex", final_filter_complex,
        "-map", current_v,
    ]

    if audio_filters:
        cmd.extend(["-filter:a", ",".join(audio_filters)])
    cmd.extend(["-map", "0:a?"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "21",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
        output_video
    ])

    print(f"[FFmpeg] Rendering 9:16 Short (Shield={anti_copyright}, Logo={bool(logo_path)})...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[FFmpeg Error] {res.stderr[-600:]}")
        return False
    return True
