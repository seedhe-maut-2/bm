import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# Your bot token (consider using environment variables instead)
BOT_TOKEN = '8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A'

async def get_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # For photos, we take the highest resolution version (last in the array)
        file = await update.message.photo[-1].get_file()
    elif update.message.video:
        # For videos
        file = await update.message.video.get_file()
    elif update.message.document:
        # For documents
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("❌ Please send a photo, video, or document.")
        return

    # Create the direct download link
    # The correct format for Telegram file link: https://api.telegram.org/file/bot<token>/<file_path>
    file_path = file.file_path  # The file_path provided by Telegram's file API
    direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    
    # Send the clean download link
    await update.message.reply_text(f"✅ Direct download link:\n{direct_link}")

def main():
    """Run the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers for different media types
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.DOCUMENT, get_direct_link))
    
    # Handler for non-media messages
    async def wrong_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Please send a photo, video, or document.")
    application.add_handler(MessageHandler(filters.ALL & ~(filters.PHOTO | filters.VIDEO | filters.DOCUMENT), wrong_format))

    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
