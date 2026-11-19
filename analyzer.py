import os
import json
import re
from typing import List, Dict, Any
from config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY

SYSTEM_PROMPT = """You are an elite YouTube Shorts & TikTok viral content strategist and video editor.
Your job is to analyze long video transcripts and extract the most VIRAL, high-retention short clips.

Criteria for a 10/10 Viral Short:
1. Hook (First 3 seconds): Must grab attention instantly with a controversial claim, unexpected question, strong emotion, or bold premise.
2. Complete Thought: The clip must make total sense standalone. Never cut off mid-thought, mid-sentence, or leave the audience confused.
3. Climax & Value: Must have an emotional peak, a punchline, a breakthrough revelation, or a high-value lesson.
4. Target Duration: Between {min_dur} and {max_dur} seconds (optimal 30-55s).

Output STRICT JSON ONLY as a list of objects with the following schema:
[
  {
    "title": "Punchy 4-7 word headline in title case",
    "start_time": float (seconds),
    "end_time": float (seconds),
    "viral_score": integer (between 70 and 99),
    "hook_text": "Exact opening words that hook the viewer",
    "reason": "Why this specific moment will trigger high retention, comments, and shares",
    "suggested_caption": "Engaging post caption including 3-5 high-traffic hashtags like #shorts #viral #fyp"
  }
]
"""

def snap_timestamps(clip_start: float, clip_end: float, segments: List[Dict]) -> tuple[float, float]:
    """Snaps AI timestamps to closest natural sentence/segment boundaries so speech isn't sliced."""
    best_start = clip_start
    best_end = clip_end

    # Find closest start
    closest_start_diff = float("inf")
    for s in segments:
        s_start = float(s["start"])
        diff = abs(s_start - clip_start)
        if diff < closest_start_diff and diff < 4.0: # within 4 seconds tolerance
            closest_start_diff = diff
            best_start = s_start

    # Find closest end
    closest_end_diff = float("inf")
    for s in segments:
        s_end = float(s["start"]) + float(s.get("duration", 2))
        diff = abs(s_end - clip_end)
        if diff < closest_end_diff and diff < 4.0:
            closest_end_diff = diff
            best_end = s_end

    if best_end <= best_start:
        best_end = best_start + 30.0

    return round(best_start, 2), round(best_end, 2)

def analyze_with_gemini(transcript_text: str, segments: List[Dict], min_dur: int, max_dur: int, max_clips: int, api_key: str = "") -> List[Dict]:
    """Uses Google Gemini (gemini-3.8-flash) to find viral moments."""
    key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("Gemini API key is required.")

    from google import genai
    client = genai.Client(api_key=key)

    prompt = (
        f"Analyze this timestamped transcript and select the top {max_clips} most viral clips "
        f"between {min_dur} and {max_dur} seconds.\n\n"
        f"TRANSCRIPT:\n{transcript_text[:50000]}"
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT.format(min_dur=min_dur, max_dur=max_dur),
            "response_mime_type": "application/json"
        }
    )

    raw_json = response.text.strip()
    clips = json.loads(raw_json)
    return clips

def analyze_with_groq(transcript_text: str, segments: List[Dict], min_dur: int, max_dur: int, max_clips: int, api_key: str = "") -> List[Dict]:
    """Uses Groq Llama-3.3-70b to find viral moments."""
    key = api_key or GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("Groq API key is required.")

    from groq import Groq
    client = Groq(api_key=key)

    prompt = (
        f"Analyze this timestamped transcript and select the top {max_clips} most viral clips "
        f"between {min_dur} and {max_dur} seconds.\n\n"
        f"TRANSCRIPT:\n{transcript_text[:35000]}"
    )

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(min_dur=min_dur, max_dur=max_dur)},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    res_text = completion.choices[0].message.content
    parsed = json.loads(res_text)
    if isinstance(parsed, dict) and "clips" in parsed:
        return parsed["clips"]
    elif isinstance(parsed, list):
        return parsed
    return list(parsed.values())[0] if parsed else []

def analyze_with_openai(transcript_text: str, segments: List[Dict], min_dur: int, max_dur: int, max_clips: int, api_key: str = "") -> List[Dict]:
    """Uses OpenAI (gpt-4o-mini) to find viral moments."""
    key = api_key or OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OpenAI API key is required.")

    from openai import OpenAI
    client = OpenAI(api_key=key)

    prompt = (
        f"Analyze this timestamped transcript and select the top {max_clips} most viral clips "
        f"between {min_dur} and {max_dur} seconds.\n\n"
        f"TRANSCRIPT:\n{transcript_text[:35000]}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(min_dur=min_dur, max_dur=max_dur)},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    parsed = json.loads(response.choices[0].message.content)
    if isinstance(parsed, dict) and "clips" in parsed:
        return parsed["clips"]
    elif isinstance(parsed, list):
        return parsed
    return list(parsed.values())[0] if parsed else []

def analyze_with_heuristic(segments: List[Dict], min_dur: int = 30, max_dur: int = 60, max_clips: int = 5) -> List[Dict]:
    """
    Intelligent heuristic fallback when no LLM API key is configured.
    Scores chunks based on hook keywords, question density, emotional words, and pace.
    """
    if not segments:
        return []

    VIRAL_KEYWORDS = {
        "secret": 3, "never": 3, "truth": 3, "mistake": 4, "money": 3, "success": 2,
        "shocking": 4, "crazy": 3, "billionaire": 3, "hack": 3, "rule": 3, "worst": 3,
        "best": 2, "stop": 3, "why": 3, "how": 2, "fail": 3, "win": 2, "nobody": 4,
        "power": 2, "danger": 3, "warning": 4, "lie": 4, "proven": 3, "change": 2
    }

    total_time = segments[-1]["start"] + segments[-1].get("duration", 2)
    step = 20.0 # Slide window by 20 seconds
    window_size = float(min_dur + max_dur) / 2.0

    candidates = []
    current_start = 0.0

    while current_start + min_dur <= total_time:
        current_end = current_start + window_size
        # Gather text in window
        window_texts = []
        for s in segments:
            s_time = float(s["start"])
            if current_start <= s_time <= current_end:
                window_texts.append(s.get("text", ""))

        full_window_text = " ".join(window_texts)
        words = full_window_text.lower().split()

        # Score window
        score = 65
        for w in words:
            clean_w = re.sub(r'[^a-z]', '', w)
            if clean_w in VIRAL_KEYWORDS:
                score += VIRAL_KEYWORDS[clean_w]

        # Question hook bonus
        if "?" in full_window_text[:80]:
            score += 8
        if "!" in full_window_text:
            score += 4

        score = min(96, score)

        if score > 70 and len(words) > 30:
            hook_words = " ".join(words[:10]).capitalize() + "..."
            title = " ".join([w.capitalize() for w in words[:5] if len(w) > 3][:4]) + " Revealed"
            candidates.append({
                "title": title or "High Engagement Moment",
                "start_time": current_start,
                "end_time": current_end,
                "viral_score": score,
                "hook_text": hook_words,
                "reason": "Contains high-potency viral keywords, emotional triggers, and strong narrative pacing.",
                "suggested_caption": f"Watch this until the end! 🔥 {title} #shorts #viral #mindset #fyp"
            })

        current_start += step

    # Sort candidates by score descending and deduplicate overlapping clips
    candidates.sort(key=lambda x: x["viral_score"], reverse=True)
    selected = []
    for c in candidates:
        overlap = False
        for s in selected:
            if abs(c["start_time"] - s["start_time"]) < 25.0:
                overlap = True
                break
        if not overlap:
            selected.append(c)
        if len(selected) >= max_clips:
            break

    return selected

def find_viral_moments(
    transcript_text: str,
    segments: List[Dict],
    min_dur: int = 30,
    max_dur: int = 60,
    max_clips: int = 5,
    preferred_provider: str = "gemini",
    api_key: str = ""
) -> List[Dict]:
    """Finds viral moments using the best available provider or falls back gracefully."""
    clips = []
    provider_used = "heuristic"

    # Try preferred provider first
    if preferred_provider == "gemini" and (api_key or GEMINI_API_KEY):
        try:
            print("[AI Analyzer] Querying Google Gemini 3.8 Flash...")
            clips = analyze_with_gemini(transcript_text, segments, min_dur, max_dur, max_clips, api_key)
            provider_used = "gemini"
        except Exception as e:
            print(f"[AI Analyzer] Gemini error: {e}, falling back...")

    elif preferred_provider == "groq" and (api_key or GROQ_API_KEY):
        try:
            print("[AI Analyzer] Querying Groq Llama-3.3...")
            clips = analyze_with_groq(transcript_text, segments, min_dur, max_dur, max_clips, api_key)
            provider_used = "groq"
        except Exception as e:
            print(f"[AI Analyzer] Groq error: {e}, falling back...")

    elif preferred_provider == "openai" and (api_key or OPENAI_API_KEY):
        try:
            print("[AI Analyzer] Querying OpenAI gpt-4o-mini...")
            clips = analyze_with_openai(transcript_text, segments, min_dur, max_dur, max_clips, api_key)
            provider_used = "openai"
        except Exception as e:
            print(f"[AI Analyzer] OpenAI error: {e}, falling back...")

    # Fallback to any configured key if preferred failed
    if not clips:
        if GEMINI_API_KEY or (preferred_provider != "gemini" and api_key):
            try:
                clips = analyze_with_gemini(transcript_text, segments, min_dur, max_dur, max_clips, api_key)
                provider_used = "gemini"
            except Exception:
                pass

    # Final intelligent heuristic fallback
    if not clips:
        print("[AI Analyzer] Using intelligent Heuristic Viral Detection engine...")
        clips = analyze_with_heuristic(segments, min_dur, max_dur, max_clips)
        provider_used = "heuristic"

    # Snap timestamps to speech boundaries
    refined_clips = []
    for c in clips:
        snapped_start, snapped_end = snap_timestamps(float(c["start_time"]), float(c["end_time"]), segments)
        dur = round(snapped_end - snapped_start, 1)
        refined_clips.append({
            "title": c.get("title", "Viral Highlight"),
            "start_time": snapped_start,
            "end_time": snapped_end,
            "duration": dur,
            "viral_score": int(c.get("viral_score", 85)),
            "hook_text": c.get("hook_text", ""),
            "reason": c.get("reason", "High viewer retention predicted."),
            "suggested_caption": c.get("suggested_caption", "#shorts #viral #fyp"),
            "provider": provider_used
        })

    return refined_clips

