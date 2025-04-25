import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg"
CHANNEL_ID = -1002512368825  # Replace with your actual channel ID

logging.basicConfig(level=logging.INFO)

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Join Channel", url="https://t.me/+RhlQLyOfQ48xMjI1")],
        [InlineKeyboardButton("Check Join", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo="https://t.me/bshshsubjsus/4",
        caption="Welcome! Please join the channel to continue.",
        reply_markup=reply_markup
    )

# Button press handler
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await query.edit_message_caption(caption="✅ You have joined the channel.")
        else:
            await query.edit_message_caption(caption="❌ You haven't joined the channel yet.")
    except Exception as e:
        await query.edit_message_caption(caption="⚠️ Error checking your join status.")

# Main function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    print("Bot is running...")
    await app.run_polling()

# Run the bot
if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
