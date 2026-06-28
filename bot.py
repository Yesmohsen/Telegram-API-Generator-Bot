import logging
import re

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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


async def _delete(update, context, msg_or_id):
    try:
        if isinstance(msg_or_id, int):
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=msg_or_id,
            )
        else:
            await msg_or_id.delete()
    except Exception:
        pass


def _phone_from_contact(update):
    phone = update.message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True, one_time_keyboard=True)

    msg = await update.message.reply_text(
        "<b>Welcome to Telegram API Bot!</b>\n\n"
        "Send me your phone number in international format\n"
        "(e.g. <code>+989123456789</code>)\n\n"
        "Or tap the button below to share your contact.",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    context.user_data["last_bot_msg"] = msg
    return PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.contact:
            phone = _phone_from_contact(update)
        else:
            phone = update.message.text.strip().replace(" ", "")

        if not phone or not phone.startswith("+"):
            await update.message.reply_text(
                "Invalid format. Send your number with country code, e.g. <code>+989123456789</code>",
                parse_mode="HTML",
            )
            return PHONE

        context.user_data["phone"] = phone

        await _delete(update, context, update.message)
        await _delete(update, context, context.user_data.get("last_bot_msg"))

        random_hash = request_tg_code_get_random_hash(phone)
        context.user_data["random_hash"] = random_hash

        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Code sent to your Telegram account! Enter the code you received.\n"
                 "You can type it or paste it.",
            reply_markup=ReplyKeyboardRemove(),
        )

        context.user_data["last_bot_msg"] = msg
        return CODE
    except Exception as e:
        logger.error(f"Error requesting code: %s", e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Failed to send code. Check your number or try again later.",
        )
        return ConversationHandler.END


def extract_code_from_text(text):
    text = text.strip()

    lines = text.strip().split("\n")
    for line in reversed(lines):
        line = line.strip()
        line = re.sub(r"^>\s*\S+\s*:\s*", "", line).strip()
        if re.match(r"^[A-Za-z0-9\-_]{4,}$", line):
            return line

    match = re.search(r"login code:\s*([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)

    words = text.split()
    if len(words) == 1:
        return text

    return text


async def ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = update.message.text or ""
        code = extract_code_from_text(raw_text)

        phone = context.user_data["phone"]
        random_hash = context.user_data["random_hash"]

        success, cookie_or_error = login_step_get_stel_cookie(phone, random_hash, code)
        if not success:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Login failed: {cookie_or_error}",
            )
            return ConversationHandler.END

        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Logging into my.telegram.org...",
        )

        await _delete(update, context, update.message)
        await _delete(update, context, context.user_data.get("last_bot_msg"))

        success, data = scarp_tg_existing_app(cookie_or_error)
        if not success:
            if "error" in data:
                await msg.edit_text(
                    f"No app found. Creating a new one...\nNote: {data['error']}"
                )
            else:
                await msg.edit_text("No app found. Creating a new one...")

            tg_hash = data.get("tg_app_hash")
            if tg_hash:
                created = create_new_tg_app(cookie_or_error, tg_hash)
                if not created:
                    await msg.edit_text(
                        "App creation failed. The shortname might already exist.\n"
                        "Please try again later or create an app manually at https://my.telegram.org"
                    )
                    return ConversationHandler.END
            else:
                await msg.edit_text(
                    "Could not create app automatically. "
                    "Please create one manually at https://my.telegram.org"
                )
                return ConversationHandler.END

            success, data = scarp_tg_existing_app(cookie_or_error)

        if success:
            await msg.edit_text(
                f"<b>Success!</b>\n\n"
                f"Phone: <code>{phone}</code>\n"
                f"API ID: <code>{data['app_id']}</code>\n"
                f"API Hash: <code>{data['api_hash']}</code>\n\n"
                "<b>Never share these with anyone!</b>",
                parse_mode="HTML",
            )
        else:
            error_msg = data.get("error", "Unknown error")
            logger.error("Failed to get credentials: %s", error_msg)
            await msg.edit_text(
                "Could not retrieve API credentials. The my.telegram.org page "
                "structure might have changed.\n"
                f"Error: {error_msg}"
            )
    except Exception as e:
        logger.error(f"Error: %s", e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"An error occurred: {e}",
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def run_bot():
    config = load_config()
    app = Application.builder().token(config["bot_token"]).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [
                MessageHandler(filters.CONTACT, ask_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone),
            ],
            CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_code),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logger.info("Bot started")
    app.run_polling()
