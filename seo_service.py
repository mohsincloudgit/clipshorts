import re
from typing import Dict, List, Any

# High-traffic base viral tags categorized by niche
NICHE_TAGS = {
    "motivation": ["motivation", "mindset", "success", "discipline", "grind", "focus", "wealth", "billionaire"],
    "tech": ["technology", "ai", "apple", "stevejobs", "future", "coding", "software", "innovation"],
    "podcast": ["podcast", "interview", "conversation", "deepdive", "wisdom", "storytime", "lifelessons"],
    "viral_core": ["shorts", "viral", "fyp", "trending", "youtubeshorts", "reels", "tiktok", "viralvideo", "foryou"]
}

def generate_viral_seo(
    title: str,
    hook_text: str,
    reason: str,
    tags_count: int = 15
) -> Dict[str, Any]:
    """
    Generates high-CTR Clickbait Titles, Viral Hashtags, and Social Captions
    specifically engineered for YouTube Shorts, Instagram Reels, and TikTok algorithms.
    """
    # Clean text to identify keywords
    combined_text = f"{title} {hook_text} {reason}".lower()

    # Determine niche keywords
    active_tags = set(NICHE_TAGS["viral_core"])
    for niche, tag_list in NICHE_TAGS.items():
        for t in tag_list:
            if t in combined_text:
                active_tags.update(tag_list[:5])
                break

    # Extract nouns / key tokens
    words = re.findall(r'[a-zA-Z]{4,}', combined_text)
    for w in words[:12]:
        if w not in ["this", "that", "with", "from", "have", "were", "they", "will", "what", "when", "your", "because"]:
            active_tags.add(w)

    tag_list = list(active_tags)[:tags_count]
    hashtags_str = " ".join([f"#{t}" for t in tag_list[:8]])
    comma_tags_str = ", ".join(tag_list)

    # 3 High-CTR Title Variants
    clean_title = re.sub(r'Revealed$', '', title).strip()
    title_variants = [
        f"Wait for the end... 🤯 | {clean_title} #shorts",
        f"Why 99% of people get this wrong! ({clean_title})",
        f"The Untold Truth About {clean_title} 🔥"
    ]

    # Platform Captions
    yt_description = (
        f"{title}\n\n"
        f"💡 Takeaway: {reason}\n\n"
        f"💬 What are your thoughts on this? Drop a comment below!\n\n"
        f"🔔 Subscribe for daily viral shorts & valuable insights!\n\n"
        f"{hashtags_str}"
    )

    ig_caption = (
        f"{title} 🔥\n\n"
        f"Double tap if this resonated with you! ❤️\n"
        f"Save this reel for later 📌\n\n"
        f"{hashtags_str}"
    )

    tiktok_caption = f"{clean_title} 🤯 What do you think? {hashtags_str}"

    return {
        "title_variants": title_variants,
        "recommended_title": title_variants[0],
        "tags_comma_separated": comma_tags_str,
        "hashtags": hashtags_str,
        "youtube_description": yt_description,
        "instagram_caption": ig_caption,
        "tiktok_caption": tiktok_caption,
        "raw_tags": tag_list
    }

