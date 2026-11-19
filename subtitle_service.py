import math
from pathlib import Path
from typing import List, Dict

ASS_HEADER_TEMPLATE = """[Script Info]
Title: Viral Short Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Preset Styles
# Note: In ASS, colors are &HAABBGGRR in hex
STYLE_HORMOZI = (
    "Style: Default,Arial Black,58,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,1,0,1,4.5,2,2,40,40,360,1"
)
STYLE_NEON = (
    "Style: Default,Impact,62,&H00FFFF00,&H0000FFFF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,2,0,1,5,0,2,40,40,360,1"
)
STYLE_MINIMAL = (
    "Style: Default,Arial,52,&H00FFFFFF,&H00AAAAAA,&H00000000,&H90000000,"
    "-1,0,0,0,100,100,0,0,1,3.5,1,2,50,50,340,1"
)

def format_ass_time(seconds: float) -> str:
    """Formats float seconds into ASS timestamp: H:MM:SS.cs"""
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def generate_ass_subtitles(
    transcript_segments: List[Dict],
    clip_start: float,
    clip_end: float,
    output_ass_path: str,
    style_name: str = "hormozi"
) -> str:
    """
    Creates an ASS subtitle file tailored for vertical 9:16 Shorts.
    Chunks speech into high-retention 3-5 word bursts.
    """
    if style_name == "neon":
        chosen_style = STYLE_NEON
    elif style_name == "minimal":
        chosen_style = STYLE_MINIMAL
    else:
        chosen_style = STYLE_HORMOZI

    events = []

    # Filter transcript items that fall inside the clip window
    relevant = []
    for item in transcript_segments:
        item_start = float(item.get("start", 0))
        item_dur = float(item.get("duration", 2))
        item_end = item_start + item_dur

        if item_end > clip_start and item_start < clip_end:
            relevant.append(item)

    # Chunk into punchy short phrases
    words_buffer = []
    chunk_start = None
    chunk_end = None

    for item in relevant:
        raw_text = item.get("text", "").strip()
        if not raw_text:
            continue

        item_start = max(0.0, float(item.get("start", 0)) - clip_start)
        item_dur = float(item.get("duration", 2))
        item_end = min(clip_end - clip_start, item_start + item_dur)

        words = raw_text.split()
        if not words:
            continue

        num_words = len(words)
        dur_per_word = item_dur / max(1, num_words)

        for i, w in enumerate(words):
            w_start = item_start + (i * dur_per_word)
            w_end = w_start + dur_per_word

            if chunk_start is None:
                chunk_start = w_start
            chunk_end = w_end
            words_buffer.append(w)

            # Emit every 3-5 words or on punctuation
            if len(words_buffer) >= 4 or w.endswith(('.', '!', '?', ',')):
                phrase = " ".join(words_buffer).upper()
                start_str = format_ass_time(chunk_start)
                end_str = format_ass_time(chunk_end)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{phrase}")
                words_buffer = []
                chunk_start = None

    # Emit leftover words
    if words_buffer and chunk_start is not None and chunk_end is not None:
        phrase = " ".join(words_buffer).upper()
        start_str = format_ass_time(chunk_start)
        end_str = format_ass_time(chunk_end)
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{phrase}")

    full_ass = ASS_HEADER_TEMPLATE.format(styles=chosen_style) + "\n".join(events) + "\n"

    Path(output_ass_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(full_ass)

    return output_ass_path

