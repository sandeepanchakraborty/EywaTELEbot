import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from session.manager import session_manager
from cache.transcript_cache import transcript_cache
from services.gemini_service import (
    generate_summary,
    generate_deep_dive,
    generate_action_points,
)
from handlers.utils import format_language_name, truncate_message

logger = logging.getLogger(__name__)

START_MESSAGE = """👋 *Welcome to YouTube AI Assistant!*

I'm your personal AI research assistant for YouTube videos.

*Here's what I can do:*

📺 *Send me a YouTube link* and I'll give you:
• 🎥 Structured summary with key points
• ⏱ Important timestamps
• 🧠 Core takeaway

💬 *Ask me questions* about the video after sharing a link

🌐 *Multi-language support* — Hindi, Kannada, Tamil, Telugu, Marathi

*Available commands:*
/summary — Get video summary
/deepdive — In-depth analysis
/actionpoints — Extract actionable items
/language — Change response language
/reset — Clear current video session
/help — Show this help message
/status — Show current session info

*Quick start:* Just paste a YouTube URL! 🚀"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_MESSAGE, parse_mode=ParseMode.MARKDOWN)

HELP_MESSAGE = """📖 *How to use YouTube AI Assistant*

*Step 1 — Share a video:*
Simply paste any YouTube URL

*Step 2 — Get summary:*
The bot automatically generates a structured summary

*Step 3 — Ask questions:*
Type any question about the video content

*Step 4 — Change language:*
Say "Summarize in Hindi" or "Explain in Kannada"

━━━━━━━━━━━━━━━━━━━━
*Commands:*
• /summary — Regenerate video summary
• /deepdive — Detailed analysis & themes
• /actionpoints — What to do after watching
• /language [lang] — Set language (e.g., /language hindi)
• /reset — Start fresh with a new video
• /status — See your current session

*Supported languages:*
🇬🇧 English (default)
🇮🇳 Hindi (हिंदी)
🇮🇳 Kannada (ಕನ್ನಡ)
🇮🇳 Tamil (தமிழ்)
🇮🇳 Telugu (తెలుగు)
🇮🇳 Marathi (मराठी)

*Tips:*
• I answer ONLY from the video content
• If something isn't in the video, I'll tell you
• Send a new URL anytime to switch videos"""

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.has_video():
        await update.message.reply_text(
            "⚠️ No video loaded yet.\n\nPlease send a YouTube URL first!"
        )
        return

    loading_msg = await update.message.reply_text("🧠 Generating summary...")

    try:
        summary = generate_summary(session.transcript, session.language)
        await loading_msg.delete()

        lang_note = ""
        if session.language != "english":
            lang_note = f"\n\n🌐 _Responding in {format_language_name(session.language)}_"

        messages = truncate_message(summary + lang_note)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Summary command failed for user {user_id}: {e}")
        await update.message.reply_text(
            f"❌ Failed to generate summary.\n\nError: {str(e)}\n\nPlease try again."
        )

async def deepdive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.has_video():
        await update.message.reply_text(
            "⚠️ No video loaded yet.\n\nPlease send a YouTube URL first!"
        )
        return

    loading_msg = await update.message.reply_text("🔬 Performing deep analysis... This may take a moment.")

    try:
        analysis = generate_deep_dive(session.transcript, session.language)
        await loading_msg.delete()

        messages = truncate_message(analysis)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Deep dive command failed for user {user_id}: {e}")
        await update.message.reply_text(
            f"❌ Failed to generate deep dive analysis.\n\nError: {str(e)}"
        )

async def actionpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.has_video():
        await update.message.reply_text(
            "⚠️ No video loaded yet.\n\nPlease send a YouTube URL first!"
        )
        return

    loading_msg = await update.message.reply_text("✅ Extracting action points...")

    try:
        actions = generate_action_points(session.transcript, session.language)
        await loading_msg.delete()

        messages = truncate_message(actions)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Action points command failed for user {user_id}: {e}")
        await update.message.reply_text(
            f"❌ Failed to extract action points.\n\nError: {str(e)}"
        )

LANGUAGE_OPTIONS = """🌐 *Choose a language:*

Type /language followed by the language name:
• `/language english` — English (default)
• `/language hindi` — Hindi (हिंदी)
• `/language kannada` — Kannada (ಕನ್ನಡ)
• `/language tamil` — Tamil (தமிழ்)
• `/language telugu` — Telugu (తెలుగు)
• `/language marathi` — Marathi (मराठी)

Or just say it naturally:
"Summarize in Hindi" or "Explain in Kannada" """

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    from config import SUPPORTED_LANGUAGES

    if not context.args:
        await update.message.reply_text(LANGUAGE_OPTIONS, parse_mode=ParseMode.MARKDOWN)
        return

    requested = context.args[0].lower()

    if requested not in SUPPORTED_LANGUAGES:
        await update.message.reply_text(
            f"❌ Unsupported language: *{requested}*\n\n"
            f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    session.set_language(requested)
    lang_display = format_language_name(requested)
    await update.message.reply_text(
        f"✅ Language set to *{lang_display}*\n\n"
        f"Future responses will be in {lang_display}.\n"
        f"Use /summary to regenerate the summary in {lang_display}.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session_manager.clear_session(user_id)
    await update.message.reply_text(
        "🔄 *Session cleared!*\n\nReady for a new video. Just send a YouTube URL!",
        parse_mode=ParseMode.MARKDOWN,
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)
    cache_stats = transcript_cache.stats

    video_info = (
        f"🎥 *Video:* {session.video_title or 'Unknown'}\n"
        f"🆔 *Video ID:* `{session.video_id}`\n"
        f"💬 *Q&A history:* {len(session.conversation_history)} exchanges\n"
    ) if session.has_video() else "📺 *No video loaded*\n"

    status_text = f"""📊 *Session Status*

{video_info}
🌐 *Language:* {format_language_name(session.language)}
⏱ *Active sessions:* {session_manager.active_sessions}

*Cache Stats:*
📦 Cached videos: {cache_stats['size']}
✅ Cache hits: {cache_stats['hits']}
❌ Cache misses: {cache_stats['misses']}
📈 Hit rate: {cache_stats['hit_rate']}"""

    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
