from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Replace this with your bot token
BOT_TOKEN = '8078721946:AAEhV6r0kXnmVaaFnRJgOk__pVjXU1mUd7A'

def get_direct_link(update: Update, context: CallbackContext):
    file = update.message.video or update.message.photo[-1] or update.message.document

    if file:
        file_info = file.get_file()
        direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        update.message.reply_text(f"✅ Direct link:\n{direct_link}")
    else:
        update.message.reply_text("❌ Please send a photo, video, or document.")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.all, get_direct_link))

    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
