# ⚡ ViralShorts AI PRO - YouTube to Viral Shorts Creator

> Turn long YouTube podcasts, interviews, speeches, and videos into high-retention, vertical **9:16 YouTube Shorts, TikToks, and Instagram Reels** with **Anti-Copyright Protection**, **Custom Branding Logos**, **Viral SEO Generation**, and **Automated Multi-Platform Scheduling**.

---

## 🌟 What's New in PRO:

### 1. 🎨 Custom Logo & Watermark Upload
- Upload your channel logo or brand watermark (PNG, JPG, WebP with transparency).
- Choose position: **Top-Right**, **Top-Left**, **Bottom-Right**, **Bottom-Left**, or **Center-Top**.
- Custom opacity blending so your branding stays sleek and professional.

### 2. 🛡️ Anti-Copyright & Monetization Shield
- **Acoustic Fingerprint Modulation**: Micro-tempo shift (`+2.5%`) and subtle equalizer tone adjustments break automated audio Content-ID matching while sounding 100% natural to human ears.
- **Visual Histogram Modulation**: Micro-zoom and subtle color grading (`eq=contrast=1.04:brightness=0.01:saturation=1.06`) shift pixel coordinates and frame hashes.
- **Fair Use Transformative Value**: Automatic 9:16 vertical background blur, dynamic animated subtitles, and custom watermarks give legal Fair Use protection and preserve monetization eligibility.

### 3. 🏷️ AI Viral SEO & Clickbait Hook Titles
- **3 Clickbait Title Variants** engineered for maximum CTR:
  - Curiosity Gap (*"Wait for the end... 🤯"*)
  - Counter-Intuitive (*"Why 99% of people get this wrong!"*)
  - Shock/Revelation (*"The Untold Truth About..."*)
- **High-Traffic Comma Tags**: Ready for YouTube tags metadata.
- **Optimized Platform Captions**: Formatted with hooks, call-to-actions, and top trending hashtags (`#shorts #viral #fyp #trending`).

### 4. 📅 Auto-Upload & Multi-Platform Scheduler
- **YouTube Shorts, Instagram Reels & TikTok**: Select any or all platforms for each clip.
- **Date & Time Picker**: Schedule clips hours or days in advance.
- **Background Daemon Worker**: Automatically monitors the queue in SQLite (`output/scheduler.db`) and executes publication when the time arrives.
- **Queue Dashboard**: Track status (`Pending ⏳`, `Published ✅`, `Failed ❌`), view publish logs, or cancel/reschedule posts with one click.

---

## 🚀 Quick Start

### 1. Launch the Web Studio
Double-click [start.bat](file:///d:/Projects/youtube%20cliping/start.bat) or run:
```bash
python web_app.py
```
Then open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📂 Project Architecture

```
youtube cliping/
├── web_app.py              # FastAPI server, REST API & Scheduler daemon
├── cli.py                  # CLI batch processor
├── pipeline.py             # Complete orchestrator
├── analyzer.py             # AI Viral Hook & Retention engine
├── ffmpeg_utils.py         # 9:16 reframing, Anti-Copyright shield & Logo overlay
├── seo_service.py          # Viral Clickbait Titles & Hashtag generator
├── publisher_service.py    # Auto-upload & SQLite scheduler engine
├── subtitle_service.py     # Hormozi style animated subtitles
├── downloader.py           # yt-dlp 1080p video downloader
├── transcript_service.py   # Fast YouTube caption retriever
├── config.py               # Paths, settings & environment
├── start.bat               # 1-click Windows launcher
├── bin/                    # Portable FFmpeg & FFprobe binaries
├── static/                 # Modern Web Studio frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
└── output/
    ├── clips/              # Finished 9:16 Shorts (.mp4, .json)
    ├── downloads/          # Cached source YouTube videos
    ├── transcripts/        # Cached transcripts
    ├── logos/              # Uploaded branding watermarks
    └── scheduler.db        # SQLite database for post scheduling
```
