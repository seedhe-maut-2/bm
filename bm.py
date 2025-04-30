import os
import base64
import asyncio
import aiohttp
import aiofiles
import math
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
CHUNK_SIZE = 65536  # 64KB chunks for downloads
MAX_FILE_SIZE = 95 * 1024 * 1024  # 95MB (under GitHub's 100MB limit)
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
                    
                    if total_size > MAX_FILE_SIZE:
                        raise Exception(f"File size {total_size/1024/1024:.2f}MB exceeds GitHub's limit")
                    
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
                await asyncio.sleep(2 ** attempt)

async def upload_large_file(file_path, file_name):
    """Upload large file by splitting into chunks"""
    chunk_size = 50 * 1024 * 1024  # 50MB chunks
    file_size = os.path.getsize(file_path)
    chunks = math.ceil(file_size / chunk_size)
    
    # Create LFS pointer file
    pointer_content = f"""version https://git-lfs.github.com/spec/v1
oid sha256:{os.popen(f'shasum -a 256 {file_path}').read().split()[0]}
size {file_size}"""
    
    # First upload the pointer file
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'message': f'Add LFS pointer for {file_name}',
        'content': base64.b64encode(pointer_content.encode()).decode('utf-8')
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.put(
            f'{GITHUB_API_URL}{file_name}',
            json=data,
            headers=headers
        ) as response:
            if response.status not in (200, 201):
                return f"❌ Failed to upload pointer file: {await response.text()}"
    
    # Here you would normally upload the actual chunks to Git LFS
    # This requires additional setup on your GitHub repo
    return f"⚠️ Large file detected ({file_size/1024/1024:.2f}MB). " \
           f"Git LFS setup required for full functionality. " \
           f"Pointer file uploaded: {file_name}"

async def upload_to_github(file_path, file_name):
    file_size = os.path.getsize(file_path)
    
    if file_size > MAX_FILE_SIZE:
        return await upload_large_file(file_path, file_name)
    
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
    
    with tqdm(total=file_size, desc=f"Uploading {file_name}", unit='B', unit_scale=True) as pbar:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f'{GITHUB_API_URL}{file_name}',
                json=data,
                headers=headers
            ) as response:
                pbar.update(file_size)
                response_data = await response.json()
    
    if response.status in (200, 201):
        return f'✅ {file_name} uploaded successfully!\n' \
               f'Size: {file_size/1024/1024:.2f} MB\n' \
               f'URL: {response_data.get("download_url", "N/A")}'
    else:
        return f'❌ Upload failed ({response.status}): {response_data.get("message", "Unknown error")}'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 Send me a video (MP4 format) and I'll upload it to GitHub!\n"
        "Note: Files >95MB require Git LFS setup."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.video:
            await update.message.reply_text("❌ Please send a video file")
            return
            
        video = update.message.video
        video_number = get_next_video_number()
        file_name = f"video{video_number}.mp4"
        
        # Check file size first
        if video.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"⚠️ File is too large ({video.file_size/1024/1024:.2f}MB).\n"
                "Please enable Git LFS in your repository or send a smaller file."
            )
            return
        
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
    print("🤖 Bot is running with large file handling...")
    app.run_polling()

if __name__ == '__main__':
    # Configure asyncio for Windows if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
