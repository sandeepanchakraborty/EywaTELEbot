import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from session.manager import session_manager
from cache.transcript_cache import transcript_cache
from services.transcript import fetch_transcript, extract_video_id, is_valid_youtube_url
from services.gemini_service import generate_summary, answer_question
from handlers.utils import (
    detect_language_request,
    is_youtube_url,
    format_language_name,
    truncate_message,
)

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    session = session_manager.get_session(user_id)

    if is_youtube_url(text):
        await _handle_youtube_url(update, context, text, session)
        return

    lang_request = detect_language_request(text)
    if lang_request:
        await _handle_language_request(update, context, lang_request, text, session)
        return

    if session.has_video():
        await _handle_question(update, context, text, session)
        return

    await update.message.reply_text(
        "👋 Please send me a YouTube URL to get started!\n\n"
        "Example:\n`https://www.youtube.com/watch?v=dQw4w9WgXcQ`\n\n"
        "Use /help to see all available commands.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def _handle_youtube_url(update, context, text, session) -> None:
    user_id = update.effective_user.id

    video_id = extract_video_id(text)
    if not video_id:
        await update.message.reply_text(
            "❌ *Invalid YouTube URL*\n\n"
            "Please send a valid YouTube link. Examples:\n"
            "• `https://youtube.com/watch?v=XXXXX`\n"
            "• `https://youtu.be/XXXXX`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    cached = transcript_cache.get(video_id)
    if cached:
        session.set_video(video_id, cached.transcript_text, f"Video {video_id}")
        status_msg = await update.message.reply_text(
            "✅ Loaded from cache!\n🧠 Generating summary..."
        )
    else:
        status_msg = await update.message.reply_text(
            "⏳ Fetching video transcript..."
        )
        try:
            transcript_result = fetch_transcript(video_id)
            transcript_cache.set(video_id, transcript_result)
            session.set_video(video_id, transcript_result.transcript_text, f"Video {video_id}")

            truncation_note = ""
            if transcript_result.is_truncated:
                truncation_note = (
                    f"\n\n⚠️ _Note: This is a long video. Summarizing the first "
                    f"{transcript_result.char_count:,} characters._"
                )

            await status_msg.edit_text(
                f"✅ Transcript fetched! ({transcript_result.char_count:,} characters)\n"
                f"🌐 Language: `{transcript_result.language}`{truncation_note}\n"
                f"🧠 Generating summary...",
                parse_mode=ParseMode.MARKDOWN,
            )

        except ValueError as e:
            await status_msg.delete()
            await update.message.reply_text(
                f"❌ *Could not process this video*\n\n{str(e)}\n\n"
                "Please try a different video.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        except Exception as e:
            await status_msg.delete()
            logger.error(f"Unexpected error for user {user_id}, video {video_id}: {e}")
            await update.message.reply_text(
                "❌ Something went wrong while fetching the transcript.\n\n"
                "Please try again in a moment.",
            )
            return

    try:
        summary = generate_summary(session.transcript, session.language)
        await status_msg.delete()

        lang_note = (
            f"\n\n🌐 _Language: {format_language_name(session.language)}_"
            if session.language != "english" else ""
        )

        header = f"🔗 `{video_id}`\n\n"
        full_response = header + summary + lang_note

        messages = truncate_message(full_response)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        await update.message.reply_text(
            "💬 *You can now ask me questions about this video!*\n\n"
            "Or use:\n"
            "• /deepdive — For detailed analysis\n"
            "• /actionpoints — For actionable items\n"
            "• /language hindi — To switch language",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        await status_msg.delete()
        logger.error(f"Summary generation failed for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Transcript fetched but summary generation failed.\n\n"
            f"Error: {str(e)}\n\n"
            "You can still ask questions about the video!"
        )

async def _handle_language_request(update, context, lang_key, original_text, session) -> None:
    session.set_language(lang_key)
    lang_name = format_language_name(lang_key)

    if session.has_video():
        loading_msg = await update.message.reply_text(
            f"🌐 Switching to {lang_name}...\n🧠 Regenerating summary..."
        )
        try:
            summary = generate_summary(session.transcript, lang_key)
            await loading_msg.delete()

            messages = truncate_message(summary)
            for msg in messages:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

            await update.message.reply_text(
                f"✅ Now responding in *{lang_name}*",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await loading_msg.delete()
            await update.message.reply_text(
                f"✅ Language set to *{lang_name}*\n\n"
                f"⚠️ But summary regeneration failed: {str(e)}\n"
                "Use /summary to try again.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        await update.message.reply_text(
            f"✅ Language set to *{lang_name}*\n\n"
            "Now send a YouTube URL and I'll respond in {lang_name}!".format(lang_name=lang_name),
            parse_mode=ParseMode.MARKDOWN,
        )

async def _handle_question(update, context, question, session) -> None:
    user_id = update.effective_user.id

    loading_msg = await update.message.reply_text("💭 Thinking...")

    try:
        answer = answer_question(
            transcript=session.transcript,
            question=question,
            conversation_history=session.conversation_history,
            language=session.language,
        )

        session.add_qa(question, answer)
        await loading_msg.delete()

        messages = truncate_message(answer)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Q&A failed for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to answer your question.\n\n"
            f"Error: {str(e)}\n\nPlease try again."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Unhandled exception: {context.error}", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An unexpected error occurred. Please try again.\n"
            "If the problem persists, use /reset to clear your session."
        )
