SYSTEM_PROMPT = """You are a creative Instagram caption writer for a personal account.
Write engaging, authentic captions that feel personal and genuine.
Include relevant hashtags at the end (5-10 hashtags).
Keep captions under 2200 characters (Instagram limit).
Use line breaks for readability. Emojis are welcome when they fit naturally."""

CONTENT_TYPE_INSTRUCTIONS = {
    "lifestyle": "Write a relatable lifestyle post. Capture everyday moments that resonate with people. Be authentic and warm.",
    "travel": "Write an exciting travel post. Share the experience, the vibe, and what makes the place special. Inspire wanderlust.",
    "food": "Write an appetizing food post. Describe the dish, the experience, or the cooking journey. Make people hungry!",
    "fitness": "Write a motivating fitness post. Share the workout, the progress, or the mindset. Inspire action without being preachy.",
    "tech": "Write an engaging tech post. Share excitement about technology, gadgets, or digital trends. Make it accessible and interesting.",
    "personal_update": "Write a heartfelt personal update. Share news, milestones, or reflections. Be genuine and connect with your audience.",
    "quote": "Write a thoughtful post around a quote or insight. Add your personal take or reflection. Make it meaningful.",
    "promotion": "Write a subtle promotional post. Highlight value without being salesy. Keep it authentic and engaging.",
}

TONE_INSTRUCTIONS = {
    "casual": "Use a relaxed, informal tone. Write like you're talking to a friend. Keep it light and easy.",
    "aesthetic": "Use a dreamy, artistic tone. Focus on vibes, mood, and visual descriptions. Be poetic but not pretentious.",
    "witty": "Use a clever, humorous tone. Add wordplay, puns, or light sarcasm. Keep it fun and entertaining.",
    "inspirational": "Use an uplifting, motivational tone. Inspire the reader and convey passion. Be genuine, not generic.",
    "informative": "Use a clear, educational tone. Share knowledge or tips. Be helpful and concise.",
    "professional": "Use a polished, professional tone. Keep it formal but approachable.",
    "friendly": "Use a warm, welcoming tone. Be conversational and positive.",
    "exciting": "Use an energetic, enthusiastic tone. Build hype and excitement!",
}


def _build_tone_instruction(tone: str) -> str:
    """Build tone instruction from comma-separated tone values."""
    tones = [t.strip() for t in tone.split(",") if t.strip()]
    if not tones:
        tones = ["casual"]
    instructions = [TONE_INSTRUCTIONS.get(t, "") for t in tones]
    return " ".join(i for i in instructions if i)


def build_prompt(content_type: str, context: str, tone: str = "casual", additional_instructions: str = "") -> str:
    parts = [
        f"Content type: {CONTENT_TYPE_INSTRUCTIONS.get(content_type, CONTENT_TYPE_INSTRUCTIONS['lifestyle'])}",
        "",
        "Platform: Instagram. Write a caption optimized for Instagram engagement. Include 5-10 relevant hashtags at the end. Use line breaks and emojis where natural.",
        "",
        f"Tone: {_build_tone_instruction(tone)}",
    ]

    if context.strip():
        parts.extend(["", f"Context/background information:\n{context}"])

    if additional_instructions.strip():
        parts.extend(["", f"Additional instructions: {additional_instructions}"])

    parts.extend(["", "Now write the Instagram caption:"])

    return "\n".join(parts)
