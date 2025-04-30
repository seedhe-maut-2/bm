import os
import requests
import base64
from telegram import Update
from telegram.ext import (
    Application,  # Replaces Updater
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# GitHub & Telegram Config (⚠️ Remove tokens before sharing code!)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # ✅ Load from environmentREVOKED! Replace with new token
GITHUB_REPO = 'seedhe-maut-2/ng'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/'
TELEGRAM_TOKEN = '7714765260:AAG4yiN5_ow25-feUeKslR2xsdeMFuPllGg'  # ⚠️ REPLACE!

async def upload_to_github(file_path, file_name):
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    data = {
        'message': 'Upload video file',
        'content': file_content_b64
    }
    
    response = requests.put(
        f'{GITHUB_API_URL}{file_name}',
        json=data,
        headers=headers
    )
    
    if response.status_code == 201:
        return f'✅ File {file_name} uploaded to GitHub!'
    else:
        return f'❌ Error: {response.json().get("message", "Unknown error")}'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Send me a video, and I'll upload it to GitHub!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    video_file = await video.get_file()
    file_name = f"{video.file_id}.mp4"
    
    await video_file.download_to_drive(file_name)  # Downloads to current directory
    response = await upload_to_github(file_name, file_name)
    
    await update.message.reply_text(response)
    os.remove(file_name)  # Cleanup

def main():
    # Create Application instead of Updater
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers (now using async/await)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
