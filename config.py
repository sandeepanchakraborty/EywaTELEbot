import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# OpenClaw local gateway (primary AI endpoint)
OPENCLAW_BASE_URL: str = os.getenv("OPENCLAW_BASE_URL", "http://127.0.0.1:18789/v1")
OPENCLAW_API_KEY: str = os.getenv("OPENCLAW_API_KEY", "")
OPENCLAW_MODEL: str = os.getenv("OPENCLAW_MODEL", "openclaw")

# Groq direct (fallback AI endpoint)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "50"))
CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "24"))
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))

SUPPORTED_LANGUAGES = {
    "english": "English",
    "hindi": "Hindi",
    "kannada": "Kannada",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "marathi": "Marathi",
}

LANGUAGE_KEYWORDS = {
    "hindi": ["hindi", "हिंदी", "हिन्दी"],
    "kannada": ["kannada", "ಕನ್ನಡ"],
    "tamil": ["tamil", "தமிழ்"],
    "telugu": ["telugu", "తెలుగు"],
    "marathi": ["marathi", "मराठी"],
    "english": ["english", "eng"],
}

MAX_TRANSCRIPT_CHARS = 15_000
CHUNK_SIZE = 6_000

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env file")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env file")
# Note: OPENCLAW_API_KEY is optional; falls back to Groq if not set
