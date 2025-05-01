import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Your bot token
BOT_TOKEN = '8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A'

async def get_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Determine the file type
    file = (update.message.video or 
            update.message.photo[-1] if update.message.photo else 
            update.message.document)

    if file:
        file_info = await file.get_file()
        direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        await update.message.reply_text(f"✅ Direct link:\n{direct_link}")
    else:
        await update.message.reply_text("❌ Please send a photo, video, or document.")

def main():
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handler
    application.add_handler(MessageHandler(filters.ALL, get_direct_link))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    # Use this simpler approach that works with the current PTB version
    main()
