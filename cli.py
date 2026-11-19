import argparse
import sys
import json
from pipeline import run_clip_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="Auto Shorts Creator - Convert long YouTube videos into viral vertical 9:16 Shorts with AI"
    )
    parser.add_argument("url", help="YouTube video URL or Video ID")
    parser.add_argument("--min-dur", type=int, default=25, help="Minimum duration for a short in seconds (default: 25)")
    parser.add_argument("--max-dur", type=int, default=60, help="Maximum duration for a short in seconds (default: 60)")
    parser.add_argument("--clips", type=int, default=3, help="Number of viral clips to cut (default: 3)")
    parser.add_argument("--mode", choices=["blur", "crop", "fit"], default="blur", help="9:16 reframe mode (default: blur)")
    parser.add_argument("--style", choices=["hormozi", "neon", "minimal", "none"], default="hormozi", help="Caption style (default: hormozi)")
    parser.add_argument("--ai", choices=["gemini", "groq", "openai", "auto"], default="gemini", help="AI provider (default: gemini)")
    parser.add_argument("--key", default="", help="Optional API key for chosen provider")

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 VIRAL SHORTS CLIPPER INITIALIZING")
    print("=" * 60)
    print(f"Target Video:    {args.url}")
    print(f"Clip Duration:   {args.min_dur}s - {args.max_dur}s")
    print(f"Clips Count:     {args.clips}")
    print(f"Layout Reframe:  {args.mode}")
    print(f"Subtitle Style:  {args.style}")
    print(f"AI Engine:       {args.ai.upper()}")
    print("=" * 60)

    try:
        def on_progress(step, pct):
            print(f"[{pct}%] {step}")

        result = run_clip_pipeline(
            url_or_file=args.url,
            min_duration=args.min_dur,
            max_duration=args.max_dur,
            max_clips=args.clips,
            reframe_mode=args.mode,
            caption_style=args.style,
            ai_provider=args.ai,
            api_key=args.key,
            progress_callback=on_progress
        )

        print("\n" + "=" * 60)
        print(f"🎉 SUCCESS: Generated {len(result['clips'])} Viral Shorts!")
        print("=" * 60)
        for i, clip in enumerate(result["clips"], 1):
            print(f"\n[{i}] {clip['title']}")
            print(f"    ⭐ Viral Score: {clip['viral_score']}/100")
            print(f"    ⏱️ Duration:    {clip['duration']}s ({clip['start_time']}s -> {clip['end_time']}s)")
            print(f"    🎣 Hook:        \"{clip['hook_text']}\"")
            print(f"    💡 Reason:      {clip['reason']}")
            print(f"    📁 File:        {clip['file_path']}")
        print("\nAll clips are ready in output/clips/ folder!")

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

