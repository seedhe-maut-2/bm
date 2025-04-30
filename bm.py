import os
import requests
import base64
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from tqdm import tqdm
import glob
import aiohttp
import aiofiles

# GitHub & Telegram Config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = 'seedhe-maut-2/ng'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/'
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHUNK_SIZE = 65536  # Increased chunk size for faster downloads

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
    # Use aiohttp for faster asynchronous downloads
    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as response:
            total_size = int(response.headers.get('content-length', 0))
            
            async with aiofiles.open(destination, 'wb') as f:
                with tqdm(
                    desc=destination,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    while True:
                        chunk = await response.content.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        await f.write(chunk)
                        bar.update(len(chunk))

async def upload_to_github(file_path, file_name):
    async with aiofiles.open(file_path, 'rb') as file:
        file_content = await file.read()
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    data = {
        'message': f'Upload {file_name}',
        'content': file_content_b64
    }
    
    with tqdm(total=os.path.getsize(file_path), desc=f"Uploading {file_name}", unit='B', unit_scale=True) as pbar:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f'{GITHUB_API_URL}{file_name}',
                json=data,
                headers=headers
            ) as response:
                pbar.update(os.path.getsize(file_path))
                response_data = await response.json()
    
    if response.status == 201:
        return f'✅ {file_name} uploaded to GitHub!\nDownload URL: {response_data.get("download_url", "")}'
    else:
        return f'❌ Error: {response_data.get("message", "Unknown error")}'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Send me a video, and I'll upload it to GitHub!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video = update.message.video
        video_number = get_next_video_number()
        file_name = f"video{video_number}.mp4"
        
        # Download with progress
        download_msg = await update.message.reply_text(f"⬇️ Downloading {file_name}...")
        video_file = await video.get_file()
        
        await download_with_progress(video_file, file_name)
        await download_msg.edit_text(f"✅ Download complete: {file_name}")
        
        # Upload with progress
        upload_msg = await update.message.reply_text(f"⬆️ Uploading {file_name} to GitHub...")
        response = await upload_to_github(file_name, file_name)
        
        await upload_msg.edit_text(response)
        
        # Cleanup
        os.remove(file_name)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        if os.path.exists(file_name):
            os.remove(file_name)

def main():
    # Clear previous downloads on startup
    for old_file in glob.glob('video*.mp4'):
        try:
            os.remove(old_file)
        except:
            pass
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    print("🤖 Bot is running with optimized download speed...")
    app.run_polling()

if __name__ == '__main__':
    # Set higher limits for aiohttp
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy() if os.name == 'nt' else asyncio.DefaultEventLoopPolicy())
    main()
