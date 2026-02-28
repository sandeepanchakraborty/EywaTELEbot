import time
import logging
from typing import Optional
from openai import OpenAI

from config import (
    OPENCLAW_BASE_URL,
    OPENCLAW_API_KEY,
    OPENCLAW_MODEL,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
    SUPPORTED_LANGUAGES,
)

logger = logging.getLogger(__name__)

# Primary: OpenClaw local gateway (routes to Groq internally via openclaw config)
_openclaw_client: Optional[OpenAI] = None
if OPENCLAW_API_KEY:
    _openclaw_client = OpenAI(
        api_key=OPENCLAW_API_KEY,
        base_url=OPENCLAW_BASE_URL,
    )
    logger.info("OpenClaw gateway client initialised at %s", OPENCLAW_BASE_URL)

# Fallback: Groq direct
_groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)

def _language_instruction(language: str) -> str:
    lang_name = SUPPORTED_LANGUAGES.get(language.lower(), "English")
    if language.lower() == "english":
        return "Respond in English."
    return (
        f"Respond entirely in {lang_name}. "
        f"All labels, headings, and content must be in {lang_name}."
    )

def _call_model(client: OpenAI, model: str, messages: list, max_tokens: int = 2048) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _generate_with_retry(messages: list, max_retries: int = 3) -> str:
    RATE_LIMIT_SIGNALS = ("rate limit", "api rate limit", "too many requests", "429")
    delays = [3, 6]

    # ── 1. Try OpenClaw gateway first ──────────────────────────────────────
    if _openclaw_client is not None:
        for attempt in range(max_retries):
            try:
                content = _call_model(_openclaw_client, OPENCLAW_MODEL, messages)
                if any(sig in content.lower() for sig in RATE_LIMIT_SIGNALS):
                    logger.warning(
                        "OpenClaw reported rate-limit in body (attempt %d), "
                        "will fall back to Groq direct.", attempt + 1
                    )
                    break  # fall through to Groq
                logger.debug("Response via OpenClaw gateway.")
                return content
            except Exception as e:
                err = str(e).lower()
                if any(x in err for x in ("429", "503", "rate", "timeout", "connection")):
                    if attempt < max_retries - 1:
                        wait = delays[attempt]
                        logger.warning(
                            "OpenClaw transient error (attempt %d), retrying in %ds: %s",
                            attempt + 1, wait, e
                        )
                        time.sleep(wait)
                        continue
                logger.warning("OpenClaw unavailable (%s), falling back to Groq direct.", e)
                break

    # ── 2. Fall back to Groq direct ───────────────────────────────────────
    logger.info("Using Groq direct endpoint.")
    for attempt in range(max_retries):
        try:
            content = _call_model(_groq_client, GROQ_MODEL, messages)
            if any(sig in content.lower() for sig in RATE_LIMIT_SIGNALS):
                if attempt < max_retries - 1:
                    wait = delays[attempt]
                    logger.warning(
                        "Groq rate-limit in response body (attempt %d), retrying in %ds...",
                        attempt + 1, wait
                    )
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    "AI service is currently rate-limited. Please try again in a moment."
                )
            return content
        except RuntimeError:
            raise
        except Exception as e:
            err_str = str(e)
            if attempt < max_retries - 1 and any(
                x in err_str.lower() for x in ("429", "503", "rate", "timeout")
            ):
                wait = delays[attempt]
                logger.warning(
                    "Groq transient error (attempt %d), retrying in %ds: %s",
                    attempt + 1, wait, err_str
                )
                time.sleep(wait)
            else:
                raise RuntimeError(err_str) from e

SUMMARY_PROMPT = """You are an expert YouTube video analyst. Analyze the following video transcript and provide a structured summary.

TRANSCRIPT:
{transcript}

Provide a structured summary with these exact sections:

🎥 **VIDEO OVERVIEW**
[2-3 sentences describing what this video is about]

📌 **5 KEY POINTS**
1. [Key point 1 with brief explanation]
2. [Key point 2 with brief explanation]
3. [Key point 3 with brief explanation]
4. [Key point 4 with brief explanation]
5. [Key point 5 with brief explanation]

⏱ **IMPORTANT TIMESTAMPS**
[List 3-5 important moments with approximate timestamps if available in transcript, or describe key transition points]

🧠 **CORE TAKEAWAY**
[The single most important insight or lesson from this video in 2-3 sentences]

💡 **WHO SHOULD WATCH**
[Briefly describe who would benefit most from this video]

{language_instruction}

Keep the summary concise but meaningful. Do not add any information not present in the transcript."""

def generate_summary(transcript: str, language: str = "english") -> str:
    prompt = SUMMARY_PROMPT.format(
        transcript=transcript,
        language_instruction=_language_instruction(language),
    )
    messages = [
        {"role": "system", "content": "You are an expert YouTube video analyst. Be concise and factual."},
        {"role": "user", "content": prompt},
    ]
    try:
        return _generate_with_retry(messages)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise RuntimeError(f"Failed to generate summary: {str(e)}")

DEEPDIVE_PROMPT = """You are an expert analyst. Perform a deep analysis of this video transcript.

TRANSCRIPT:
{transcript}

Provide an in-depth analysis:

🔬 **DEEP DIVE ANALYSIS**

**Main Arguments & Evidence**
[List the main arguments made and evidence provided]

**Methodologies or Frameworks Mentioned**
[Any specific methods, frameworks, or systems discussed]

**Data & Statistics**
[Any numbers, statistics, or data points mentioned]

**Expert Opinions & Quotes**
[Notable quotes or expert perspectives]

**Controversies or Counterpoints**
[Any opposing views or debates addressed]

**Practical Applications**
[How the information can be applied in real life]

{language_instruction}

Base your analysis strictly on the transcript content."""

def generate_deep_dive(transcript: str, language: str = "english") -> str:
    prompt = DEEPDIVE_PROMPT.format(
        transcript=transcript,
        language_instruction=_language_instruction(language),
    )
    messages = [
        {"role": "system", "content": "You are an expert analyst. Analyze strictly based on the provided content."},
        {"role": "user", "content": prompt},
    ]
    try:
        return _generate_with_retry(messages)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Deep dive failed: {e}")
        raise RuntimeError(f"Failed to generate deep dive: {str(e)}")

ACTION_POINTS_PROMPT = """You are a productivity expert. Extract actionable items from this video transcript.

TRANSCRIPT:
{transcript}

Extract clear, actionable items:

✅ **ACTION POINTS**

**Immediate Actions (Do Today)**
• [Action 1]
• [Action 2]
• [Action 3]

**Short-term Actions (This Week)**
• [Action 1]
• [Action 2]

**Long-term Actions (This Month/Year)**
• [Action 1]
• [Action 2]

**Resources Mentioned**
• [Books, tools, websites, or resources referenced]

**Key People/Organizations to Follow**
• [Any experts or organizations mentioned worth following]

{language_instruction}

Only extract actions explicitly mentioned or strongly implied in the transcript."""

def generate_action_points(transcript: str, language: str = "english") -> str:
    prompt = ACTION_POINTS_PROMPT.format(
        transcript=transcript,
        language_instruction=_language_instruction(language),
    )
    messages = [
        {"role": "system", "content": "You are a productivity expert extracting action items from video content."},
        {"role": "user", "content": prompt},
    ]
    try:
        return _generate_with_retry(messages)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Action points failed: {e}")
        raise RuntimeError(f"Failed to generate action points: {str(e)}")

QA_SYSTEM_PROMPT = """You are a helpful assistant answering questions about a YouTube video.
IMPORTANT RULES:
- Answer ONLY based on information in the transcript provided by the user
- Do NOT use any external knowledge or make assumptions
- If the answer is not in the transcript, respond with exactly: "\u274c This topic is not covered in the video."
- Be concise but complete
- Do not hallucinate"""

QA_USER_PROMPT = """VIDEO TRANSCRIPT:
{transcript}

CONVERSATION HISTORY:
{history}

USER QUESTION: {question}

{language_instruction}"""

def answer_question(
    transcript: str,
    question: str,
    conversation_history: list[dict],
    language: str = "english",
) -> str:
    history_text = ""
    if conversation_history:
        history_lines = []
        for item in conversation_history[-5:]:
            history_lines.append(f"Q: {item['q']}")
            history_lines.append(f"A: {item['a']}")
        history_text = "\n".join(history_lines)
    else:
        history_text = "No previous conversation."

    user_prompt = QA_USER_PROMPT.format(
        transcript=transcript,
        history=history_text,
        question=question,
        language_instruction=_language_instruction(language),
    )
    messages = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    try:
        return _generate_with_retry(messages)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise RuntimeError(f"Failed to answer question: {str(e)}")

def detect_language_from_text(text: str) -> Optional[str]:
    messages = [
        {
            "role": "system",
            "content": (
                "You detect language requests in user messages. "
                "Respond with ONLY one word from: english, hindi, kannada, tamil, telugu, marathi, none"
            ),
        },
        {
            "role": "user",
            "content": (
                f'The user sent: "{text}"\n'
                "Is the user requesting a response in a specific language? "
                "If yes, which one? If no language request, respond: none"
            ),
        },
    ]
    try:
        result = _generate_with_retry(messages).lower().strip()
        if result in ["english", "hindi", "kannada", "tamil", "telugu", "marathi"]:
            return result
        return None
    except Exception:
        return None
