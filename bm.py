import os
import requests
import base64
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from tqdm import tqdm  # For progress bars
import glob

# GitHub & Telegram Config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = 'seedhe-maut-2/ng'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/'
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Video counter initialization
if not os.path.exists('counter.txt'):
    with open('counter.txt', 'w') as f:
        f.write('0')

def get_next_video_number():
    with open('counter.txt', 'r+') as f:
        count = int(f.read())
        f.seek(0)
        f.write(str(count + 1))
        return count + 1

async def download_with_progress(file, destination):
    response = requests.get(file.file_path, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as f, tqdm(
        desc=destination,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            bar.update(len(data))

async def upload_to_github(file_path, file_name):
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    data = {
        'message': f'Upload {file_name}',
        'content': file_content_b64
    }
    
    with tqdm(total=os.path.getsize(file_path), desc=f"Uploading {file_name}", unit='B', unit_scale=True) as pbar:
        response = requests.put(
            f'{GITHUB_API_URL}{file_name}',
            json=data,
            headers=headers
        )
        pbar.update(os.path.getsize(file_path))
    
    if response.status_code == 201:
        return f'✅ {file_name} uploaded to GitHub!'
    else:
        return f'❌ Error: {response.json().get("message", "Unknown error")}'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Send me a video, and I'll upload it to GitHub!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    video_number = get_next_video_number()
    file_name = f"video{video_number}.mp4"
    
    # Download with progress
    await update.message.reply_text(f"⬇️ Downloading {file_name}...")
    video_file = await video.get_file()
    await download_with_progress(video_file, file_name)
    
    # Upload with progress
    await update.message.reply_text(f"⬆️ Uploading {file_name} to GitHub...")
    response = await upload_to_github(file_name, file_name)
    
    await update.message.reply_text(response)
    os.remove(file_name)  # Cleanup

def main():
    # Clear previous downloads on startup
    for old_file in glob.glob('video*.mp4'):
        os.remove(old_file)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    print("🤖 Bot is running with progress tracking...")
    app.run_polling()

if __name__ == '__main__':
    main()
