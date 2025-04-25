from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
import asyncio

BOT_TOKEN = "7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg"
CHANNEL_ID = -1002512368825  # Your channel ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Join Channel", url="https://t.me/+RhlQLyOfQ48xMjI1")],
        [InlineKeyboardButton("Check Join", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Please join the channel to continue.",
        reply_markup=reply_markup
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await query.answer("You have joined the channel!")
            await query.edit_message_text("✅ You have joined the channel.")
        else:
            await query.answer("You haven't joined yet!")
            await query.edit_message_text("❌ You haven't joined the channel yet.")
    except Exception as e:
        await query.answer("Error checking join status.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
