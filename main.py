import logging
import sys

from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers.commands import (
    start_command,
    help_command,
    summary_command,
    deepdive_command,
    actionpoints_command,
    language_command,
    reset_command,
    status_command,
)
from handlers.messages import handle_message, error_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("summary", "Get video summary"),
        BotCommand("deepdive", "In-depth analysis"),
        BotCommand("actionpoints", "Extract action items"),
        BotCommand("language", "Change response language"),
        BotCommand("reset", "Clear current session"),
        BotCommand("status", "Show session info"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered successfully")

def main() -> None:
    logger.info("Starting YouTube AI Telegram Bot...")

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("deepdive", deepdive_command))
    application.add_handler(CommandHandler("actionpoints", actionpoints_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("status", status_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.add_error_handler(error_handler)

    logger.info("Bot is running in polling mode. Press Ctrl+C to stop.")
    application.run_polling(
        allowed_updates=["message"],
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
