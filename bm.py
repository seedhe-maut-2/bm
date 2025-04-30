import os
import base64
import asyncio
import aiohttp
import aiofiles
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

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = 'seedhe-maut-2/ng'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/'
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHUNK_SIZE = 65536  # 64KB chunks for faster downloads
MAX_RETRIES = 3

# Initialize video counter
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
    async with aiohttp.ClientSession() as session:
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(file.file_path) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP Error {response.status}")
                    
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
                    return True
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def upload_to_github(file_path, file_name):
    async with aiofiles.open(file_path, 'rb') as file:
        file_content = await file.read()
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Check if file exists to get SHA
    sha = None
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'{GITHUB_API_URL}{file_name}',
            headers=headers
        ) as response:
            if response.status == 200:
                existing_file = await response.json()
                sha = existing_file.get('sha')
    
    data = {
        'message': f'Upload {file_name}',
        'content': file_content_b64
    }
    if sha:
        data['sha'] = sha
    
    with tqdm(total=os.path.getsize(file_path), desc=f"Uploading {file_name}", unit='B', unit_scale=True) as pbar:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f'{GITHUB_API_URL}{file_name}',
                json=data,
                headers=headers
            ) as response:
                pbar.update(os.path.getsize(file_path))
                response_data = await response.json()
    
    if response.status in (200, 201):
        return f'✅ {file_name} uploaded successfully!\n' \
               f'Size: {os.path.getsize(file_path)/1024/1024:.2f} MB\n' \
               f'URL: {response_data.get("download_url", "N/A")}'
    else:
        return f'❌ Upload failed ({response.status}): {response_data.get("message", "Unknown error")}'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Send me a video (MP4 format) and I'll upload it to GitHub!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.video:
            await update.message.reply_text("❌ Please send a video file")
            return
            
        video = update.message.video
        video_number = get_next_video_number()
        file_name = f"video{video_number}.mp4"
        
        # Download with progress
        status_msg = await update.message.reply_text(
            f"⬇️ Downloading video {video_number}...\n"
            f"File: {file_name}\n"
            f"Size: {video.file_size/1024/1024:.2f} MB"
        )
        
        try:
            video_file = await video.get_file()
            await download_with_progress(video_file, file_name)
            await status_msg.edit_text(
                f"✅ Download complete!\n"
                f"Now uploading to GitHub..."
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ Download failed: {str(e)}")
            return
        
        # Upload to GitHub
        try:
            result = await upload_to_github(file_name, file_name)
            await update.message.reply_text(result)
        except Exception as e:
            await update.message.reply_text(f"❌ GitHub upload failed: {str(e)}")
        
        # Cleanup
        try:
            os.remove(file_name)
        except:
            pass
            
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

def main():
    # Clean up old files
    for old_file in glob.glob('video*.mp4'):
        try:
            os.remove(old_file)
        except:
            pass
    
    # Create bot application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Run bot
    print("🤖 Bot is running with optimized performance...")
    app.run_polling()

if __name__ == '__main__':
    # Configure asyncio for Windows if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
