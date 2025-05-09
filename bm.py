import os
from mega import Mega
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = '7818864949:AAEpqPVZj4oUAl2hFyiTSbZqfbzDr3TQ9fw'  # ← Replace this

MEGA_FOLDER_LINK = 'https://mega.nz/folder/jLYiRSjT#NwiJV5JrRLMZ5qQacUGOvA'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MEGA folder se videos download ho rahe hain...")

    # MEGA login
    mega = Mega()
    m = mega.login()

    # Folder se files download
    folder = m._parse_url(MEGA_FOLDER_LINK)
    files = m.get_files_in_node(folder['node'])

    download_dir = "downloaded_videos"
    os.makedirs(download_dir, exist_ok=True)

    for file_id in files:
        file_info = files[file_id]
        file_name = file_info['a']['n']
        file_size = int(file_info['s']) / (1024 * 1024)

        # Sirf video file jaise mp4/mkv download karo
        if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            await update.message.reply_text(f"Downloading: {file_name} ({file_size:.2f} MB)")
            m.download(file_info, dest_filename=file_name, dest_path=download_dir)

            file_path = os.path.join(download_dir, file_name)
            with open(file_path, 'rb') as f:
                await update.message.reply_video(f, caption=file_name)

    await update.message.reply_text("Sabhi videos upload ho gaye.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
