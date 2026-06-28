import logging
import random

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import load_config
from scraper import (
    create_new_tg_app,
    login_step_get_stel_cookie,
    request_tg_code_get_random_hash,
    scarp_tg_existing_app,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PHONE, CODE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me your phone number in international format "
        "(e.g. +989123456789)\n\n"
        "I'll get your API ID and API Hash from my.telegram.org.\n"
        "Send /cancel to abort."
    )
    return PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip().replace(" ", "")
    if not phone.startswith("+"):
        await update.message.reply_text(
            "Invalid format. Send your number with country code, e.g. +989123456789"
        )
        return PHONE

    context.user_data["phone"] = phone
    await update.message.reply_text("Requesting code from Telegram...")

    try:
        random_hash = request_tg_code_get_random_hash(phone)
        context.user_data["random_hash"] = random_hash
        await update.message.reply_text(
            "Code sent to your Telegram account! Enter the code you received."
        )
        return CODE
    except Exception as e:
        logger.error(f"Error requesting code: {e}")
        await update.message.reply_text(
            "Failed to send code. Check your number or try again later."
        )
        return ConversationHandler.END


async def ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    phone = context.user_data["phone"]
    random_hash = context.user_data["random_hash"]

    await update.message.reply_text("Logging into my.telegram.org...")

    try:
        success, cookie_or_error = login_step_get_stel_cookie(
            phone, random_hash, code
        )
        if not success:
            await update.message.reply_text(f"Login failed: {cookie_or_error}")
            return ConversationHandler.END

        success, data = scarp_tg_existing_app(cookie_or_error)
        if not success:
            await update.message.reply_text("No app found. Creating a new one...")
            tg_hash = data.get("tg_app_hash")
            create_new_tg_app(cookie_or_error, tg_hash)
            success, data = scarp_tg_existing_app(cookie_or_error)

        if success:
            await update.message.reply_text(
                f"Success!\n\n"
                f"Phone: {phone}\n"
                f"API ID: {data['app_id']}\n"
                f"API Hash: {data['api_hash']}\n\n"
                "Never share these with anyone!"
            )
        else:
            await update.message.reply_text("Failed to get API credentials.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"An error occurred: {e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def run_bot():
    config = load_config()
    app = Application.builder().token(config["bot_token"]).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)
            ],
            CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_code)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logger.info("Bot started")
    app.run_polling()
