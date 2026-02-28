import re
import logging
from typing import Optional

from config import LANGUAGE_KEYWORDS, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

def detect_language_request(text: str) -> Optional[str]:
    text_lower = text.lower()
    for lang_key, keywords in LANGUAGE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return lang_key
    return None

def is_youtube_url(text: str) -> bool:
    yt_patterns = [
        r"youtube\.com/watch",
        r"youtu\.be/",
        r"youtube\.com/shorts/",
        r"youtube\.com/embed/",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in yt_patterns)

def format_language_name(lang_key: str) -> str:
    return SUPPORTED_LANGUAGES.get(lang_key.lower(), "English")

def truncate_message(text: str, max_length: int = 4096) -> list[str]:
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        split_at = text.rfind("\n\n", 0, max_length)
        if split_at == -1:
            split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()

    return parts

def loading_message(action: str = "Processing") -> str:
    messages = {
        "transcript": "⏳ Fetching video transcript...",
        "summary": "🧠 Generating summary... This may take a moment.",
        "deepdive": "🔬 Performing deep analysis... Please wait.",
        "actionpoints": "✅ Extracting action points...",
        "qa": "💭 Thinking...",
        "translate": "🌐 Translating...",
    }
    return messages.get(action, f"⏳ {action}...")
