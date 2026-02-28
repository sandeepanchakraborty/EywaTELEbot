import re
import logging
from typing import Optional
from dataclasses import dataclass

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
    RequestBlocked,
    IpBlocked,
)

from config import MAX_TRANSCRIPT_CHARS, CHUNK_SIZE

logger = logging.getLogger(__name__)

_yt_api = YouTubeTranscriptApi()

_YT_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
]

@dataclass
class TranscriptResult:
    video_id: str
    transcript_text: str
    language: str
    is_truncated: bool
    chunks: list[str]
    char_count: int

def extract_video_id(url: str) -> Optional[str]:
    url = url.strip()
    for pattern in _YT_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_valid_youtube_url(url: str) -> bool:
    return extract_video_id(url) is not None

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    overlap = 500
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        last_period = chunk.rfind(". ")
        if last_period > chunk_size // 2:
            chunk = chunk[: last_period + 1]
            end = start + last_period + 1
        chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def _snippets_to_text(entries) -> str:
    parts = []
    for entry in entries:
        if isinstance(entry, dict):
            parts.append(entry.get("text", ""))
        else:
            parts.append(getattr(entry, "text", str(entry)))
    return " ".join(p.strip() for p in parts if p.strip())

def fetch_transcript(video_id: str) -> TranscriptResult:
    try:
        try:
            fetched = _yt_api.fetch(video_id, languages=["en", "en-US", "en-GB"])
            language_code = "en"
            full_text = _snippets_to_text(fetched)
        except (NoTranscriptFound, CouldNotRetrieveTranscript):
            transcript_list = _yt_api.list(video_id)
            available = list(transcript_list)

            if not available:
                raise ValueError("No captions available for this video.")

            transcript = None
            for t in available:
                if not t.is_generated:
                    transcript = t
                    break
            if transcript is None:
                transcript = available[0]

            language_code = transcript.language_code

            if transcript.is_translatable and not language_code.startswith("en"):
                try:
                    transcript = transcript.translate("en")
                    language_code = f"{language_code}→en"
                except Exception:
                    pass

            fetched = transcript.fetch()
            full_text = _snippets_to_text(fetched)

        if not full_text.strip():
            raise ValueError("Transcript is empty for this video.")

        is_truncated = len(full_text) > MAX_TRANSCRIPT_CHARS
        if is_truncated:
            logger.info(
                f"Long transcript for {video_id} ({len(full_text)} chars), "
                f"using first {MAX_TRANSCRIPT_CHARS} chars."
            )
            process_text = full_text[:MAX_TRANSCRIPT_CHARS]
        else:
            process_text = full_text

        chunks = _chunk_text(process_text)

        return TranscriptResult(
            video_id=video_id,
            transcript_text=process_text,
            language=language_code,
            is_truncated=is_truncated,
            chunks=chunks,
            char_count=len(process_text),
        )

    except ValueError:
        raise
    except VideoUnavailable:
        raise ValueError(
            "This video is unavailable or private. Please check the URL and try again."
        )
    except TranscriptsDisabled:
        raise ValueError(
            "Transcripts are disabled for this video. The creator has turned off captions."
        )
    except NoTranscriptFound:
        raise ValueError(
            "No transcript found for this video. It may not have captions available."
        )
    except (RequestBlocked, IpBlocked):
        raise ValueError(
            "YouTube is temporarily blocking transcript requests. Please try again in a few minutes."
        )
    except CouldNotRetrieveTranscript as e:
        raise ValueError(f"Could not retrieve transcript: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching transcript for {video_id}: {e}")
        raise ValueError(f"Could not fetch transcript: {str(e)}")
