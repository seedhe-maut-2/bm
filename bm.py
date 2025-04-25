from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import telegram

# Replace with your bot token
BOT_TOKEN = "7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg"
CHANNEL_ID = -1002512368825  # Your channel ID

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Join Channel", url="https://t.me/+RhlQLyOfQ48xMjI1")],
        [InlineKeyboardButton("Check Join", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id

    # Send text message (no photo)
    context.bot.send_message(
        chat_id=chat_id,
        text="Welcome! Please join the channel to continue.",
        reply_markup=reply_markup
    )

def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            query.answer("You have joined the channel!")
            query.edit_message_text("✅ You have joined the channel.")
        else:
            query.answer("You haven't joined yet!")
            query.edit_message_text("❌ You haven't joined the channel yet.")
    except telegram.error.TelegramError:
        query.answer("Error checking join status.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
