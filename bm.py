import os
import subprocess
import sys
import asyncio
import signal
from datetime import datetime
import time
from collections import deque
import aiofiles
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force install required packages with --break-system-packages
required = ['telethon', 'tqdm', 'aiofiles', 'aiohttp']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        logger.info(f"Installing {pkg}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", pkg])
        except subprocess.CalledProcessError:
            logger.error(f"Failed to install {pkg}")
            sys.exit(1)

from telethon.sync import TelegramClient, events
from telethon.tl.types import Document, DocumentAttributeVideo
from tqdm import tqdm

# Configuration
class Config:
    def __init__(self):
        self.api_id = 22625636  # Replace with your API ID
        self.api_hash = 'f71778a6e1e102f33ccc4aee3b5cc697'  # Replace with your API Hash
        self.session_name = 'stream_bot_session'
        self.bot_token = '7710269508:AAGTZlpf_GBpwh2kILwUjzE6gys4EgdYmDk'  # Replace with your bot token
        self.allowed_user_ids = [8167507955]  # Replace with your user ID
        self.video_queue = deque(maxlen=10)  # Store up to 10 videos
        self.current_video_index = 0
        self.rtmp_url = 'rtmps://dc5-1.rtmp.t.me/s/2577781115:yTl41OgfjFRzupdXO1YLLQ'
        self.stream_process = None
        self.stream_start_time = None
        self.download_chunk_size = 1024 * 1024  # 1MB chunks
        self.max_parallel_downloads = 3
        self.video_storage = "videos"
        self.ffmpeg_preset = 'veryfast'
        self.stream_resolution = '1280:720'
        self.stream_bitrate = '3000k'
        self.stream_buffer = '6000k'
        
        os.makedirs(self.video_storage, exist_ok=True)

config = Config()

# Initialize Telegram client
try:
    client = TelegramClient(config.session_name, config.api_id, config.api_hash)
    bot = TelegramClient('bot', config.api_id, config.api_hash).start(bot_token=config.bot_token)
    logger.info("Telegram clients initialized")
except Exception as e:
    logger.error(f"Failed to initialize Telegram clients: {e}")
    sys.exit(1)

async def download_file_part(session, url, start, end, filename):
    """Download a part of the file using aiohttp"""
    headers = {'Range': f'bytes={start}-{end}'}
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            async with aiofiles.open(filename, 'rb+') as f:
                await f.seek(start)
                async for chunk in response.content.iter_chunked(config.download_chunk_size):
                    await f.write(chunk)
    except Exception as e:
        logger.error(f"Error downloading part {start}-{end}: {e}")
        raise

async def parallel_download(file_path, file_size, download_url):
    """Download file in parallel chunks"""
    part_size = file_size // config.max_parallel_downloads
    
    # Create empty file of full size
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.truncate(file_size)
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        raise
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(config.max_parallel_downloads):
            start = i * part_size
            end = (i + 1) * part_size - 1 if i < config.max_parallel_downloads - 1 else file_size - 1
            tasks.append(download_file_part(session, download_url, start, end, file_path))
        
        await asyncio.gather(*tasks)

async def download_video(channel_username, message_id):
    """Download video from Telegram message with parallel downloads"""
    try:
        logger.info(f"Starting download from {channel_username} message {message_id}")
        
        # Verify channel access first
        try:
            channel_entity = await client.get_entity(channel_username)
            logger.info(f"Channel verified: {channel_entity.title}")
        except Exception as e:
            logger.error(f"Channel access error: {e}")
            return None
            
        msg = await client.get_messages(channel_username, ids=message_id)
        
        if not msg:
            logger.error("Message not found")
            return None
            
        if not msg.media:
            logger.error("Message has no media")
            return None
            
        if not isinstance(msg.media, Document):
            logger.error("Message media is not a document")
            return None
            
        video_attrs = [attr for attr in msg.document.attributes if isinstance(attr, DocumentAttributeVideo)]
        if not video_attrs:
            logger.error("No video attributes found")
            return None
            
        total_size = msg.document.size
        logger.info(f"Video size: {total_size/1024/1024:.2f} MB")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}_{message_id}.mp4"
        file_path = os.path.join(config.video_storage, filename)
        
        # Get download URL
        try:
            download_url = await client.download_media(msg.document, file=file_path)
            logger.info(f"Download URL obtained, starting parallel download")
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return None
            
        # Download using parallel method
        try:
            await parallel_download(file_path, total_size, download_url)
            logger.info("Parallel download completed successfully")
        except Exception as e:
            logger.error(f"Parallel download failed: {e}")
            try:
                os.remove(file_path)
            except:
                pass
            return None
            
        # Add to video queue
        video_info = {
            'path': file_path,
            'channel': channel_username,
            'message_id': message_id,
            'size': total_size,
            'duration': video_attrs[0].duration if video_attrs else 0,
            'timestamp': timestamp
        }
        config.video_queue.append(video_info)
        config.current_video_index = len(config.video_queue) - 1
        
        return file_path
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

async def start_stream(video_index=None):
    """Start streaming the specified video"""
    try:
        if not config.video_queue:
            return False, "❌ No videos available. Please download first using /download."
        
        video_index = config.current_video_index if video_index is None else video_index
        
        try:
            video_info = config.video_queue[video_index]
        except IndexError:
            return False, "❌ Invalid video index."
            
        if not os.path.exists(video_info['path']):
            return False, "❌ Video file not found."
        
        if config.stream_process and config.stream_process.poll() is None:
            return False, "❌ Stream is already running."
        
        ffmpeg_command = [
            'ffmpeg',
            '-re',
            '-i', video_info['path'],
            '-vf', f'scale={config.stream_resolution}',
            '-c:v', 'libx264',
            '-preset', config.ffmpeg_preset,
            '-maxrate', config.stream_bitrate,
            '-bufsize', config.stream_buffer,
            '-pix_fmt', 'yuv420p',
            '-g', '50',
            '-c:a', 'aac',
            '-b:a', '160k',
            '-ar', '44100',
            '-f', 'flv',
            config.rtmp_url
        ]
        
        try:
            logger.info(f"Starting FFmpeg stream: {' '.join(ffmpeg_command)}")
            config.stream_process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            config.stream_start_time = datetime.now()
            config.current_video_index = video_index
            return True, f"✅ Streaming: {os.path.basename(video_info['path'])}"
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return False, f"❌ FFmpeg error: {str(e)}"
            
    except Exception as e:
        logger.error(f"Stream error: {e}")
        return False, f"❌ Stream error: {str(e)}"

async def stop_stream():
    """Stop the current stream"""
    try:
        if not config.stream_process:
            return False, "❌ No active stream to stop."
            
        logger.info("Stopping stream...")
        config.stream_process.terminate()
        try:
            config.stream_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            config.stream_process.kill()
        
        stream_duration = datetime.now() - config.stream_start_time if config.stream_start_time else None
        message = "✅ Stream stopped."
        if stream_duration:
            message += f"\n⏱ Duration: {str(stream_duration).split('.')[0]}"
        
        config.stream_process = None
        config.stream_start_time = None
        return True, message
        
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        return False, f"❌ Error stopping stream: {str(e)}"

def is_user_allowed(user_id):
    """Check if user is allowed to control the bot"""
    return user_id in config.allowed_user_ids

async def cleanup_videos():
    """Clean up old video files"""
    try:
        while len(config.video_queue) > 5:
            old_video = config.video_queue.popleft()
            try:
                if os.path.exists(old_video['path']):
                    os.remove(old_video['path'])
                    logger.info(f"Cleaned up old video: {old_video['path']}")
            except Exception as e:
                logger.error(f"Error deleting file {old_video['path']}: {e}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# Bot command handlers
@bot.on(events.NewMessage(pattern='/start|/help'))
async def start_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    help_text = """
🤖 **Enhanced Telegram Stream Bot** 🤖

Available commands:
- /download [channel] [message_id] - Download video
- /startstream [index] - Start streaming
- /stopstream - Stop current stream
- /listvideos - Show available videos
- /playvideo [index] - Switch video
- /deletevideo [index] - Delete video
- /status - Show current status
- /setrtmp [url] - Update RTMP URL
- /settings - Show settings
- /help - Show this help
"""
    await event.reply(help_text)

@bot.on(events.NewMessage(pattern='/download'))
async def download_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    args = event.message.text.split()
    if len(args) != 3:
        await event.reply("❌ Usage: /download channel_username message_id")
        return
    
    try:
        channel = args[1]
        message_id = int(args[2])
        
        progress_msg = await event.reply(f"⏳ Starting download from {channel} (message {message_id})...")
        
        # Verify channel first
        try:
            entity = await client.get_entity(channel)
            await progress_msg.edit(f"🔍 Found channel: {entity.title}\nStarting download...")
        except Exception as e:
            await progress_msg.edit(f"❌ Channel error: {str(e)}")
            return
            
        file_path = await download_video(channel, message_id)
        if file_path:
            await progress_msg.edit(
                f"✅ Download successful!\n"
                f"📁 Path: `{file_path}`\n"
                f"💾 Size: {os.path.getsize(file_path)/1024/1024:.2f} MB\n"
                f"Now you can /startstream"
            )
            await cleanup_videos()
        else:
            await progress_msg.edit("❌ Download failed. Possible reasons:\n"
                                  "1. Invalid message ID\n"
                                  "2. No video in message\n"
                                  "3. Access denied")
    except ValueError:
        await event.reply("❌ Message ID must be a number")
    except Exception as e:
        logger.error(f"Download handler error: {e}")
        await event.reply(f"❌ Unexpected error: {str(e)}")

@bot.on(events.NewMessage(pattern='/startstream'))
async def start_stream_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    args = event.message.text.split()
    video_index = None
    if len(args) > 1:
        try:
            video_index = int(args[1])
        except ValueError:
            await event.reply("❌ Invalid video index")
            return
    
    message = await event.reply("🔄 Starting stream...")
    success, result = await start_stream(video_index)
    await message.edit(result)

@bot.on(events.NewMessage(pattern='/stopstream'))
async def stop_stream_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    message = await event.reply("🔄 Stopping stream...")
    success, result = await stop_stream()
    await message.edit(result)

@bot.on(events.NewMessage(pattern='/listvideos'))
async def list_videos_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    if not config.video_queue:
        await event.reply("ℹ️ No videos available. Use /download first.")
        return
    
    response = ["📹 Available Videos (use /playvideo [index] to switch):"]
    for idx, video in enumerate(config.video_queue):
        current_marker = " (🟢 Current)" if idx == config.current_video_index else ""
        size_mb = video['size'] / (1024 * 1024)
        duration = time.strftime('%H:%M:%S', time.gmtime(video['duration']))
        response.append(
            f"{idx}: {os.path.basename(video['path'])} "
            f"[{size_mb:.1f}MB, {duration}]{current_marker}"
        )
    
    await event.reply("\n".join(response))

@bot.on(events.NewMessage(pattern='/playvideo'))
async def play_video_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    args = event.message.text.split()
    if len(args) != 2:
        await event.reply("❌ Usage: /playvideo [index]")
        return
    
    try:
        video_index = int(args[1])
        if video_index < 0 or video_index >= len(config.video_queue):
            await event.reply("❌ Invalid video index")
            return
        
        # Stop current stream if running
        if config.stream_process and config.stream_process.poll() is None:
            await stop_stream()
        
        config.current_video_index = video_index
        await event.reply(f"✅ Selected video {video_index}. Use /startstream to begin streaming.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/deletevideo'))
async def delete_video_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    args = event.message.text.split()
    if len(args) != 2:
        await event.reply("❌ Usage: /deletevideo [index]")
        return
    
    try:
        video_index = int(args[1])
        if video_index < 0 or video_index >= len(config.video_queue):
            await event.reply("❌ Invalid video index")
            return
        
        if (config.stream_process and config.stream_process.poll() is None and 
            video_index == config.current_video_index):
            await event.reply("❌ Can't delete currently streaming video. Stop stream first.")
            return
        
        video_to_delete = config.video_queue[video_index]
        try:
            if os.path.exists(video_to_delete['path']):
                os.remove(video_to_delete['path'])
            del config.video_queue[video_index]
            
            if config.current_video_index >= video_index:
                config.current_video_index = max(0, config.current_video_index - 1)
            
            await event.reply(f"✅ Deleted video {video_index}")
        except Exception as e:
            await event.reply(f"❌ Error deleting file: {str(e)}")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    status = ["📊 **Current Status**"]
    
    if config.video_queue:
        current_video = config.video_queue[config.current_video_index]
        status.append(f"📹 Current Video: {os.path.basename(current_video['path'])}")
        status.append(f"📦 Size: {current_video['size']/1024/1024:.1f}MB")
        status.append(f"⏱ Duration: {time.strftime('%H:%M:%S', time.gmtime(current_video['duration']))}")
    
    if config.stream_process and config.stream_process.poll() is None:
        status.append("🔴 Stream: Running")
        if config.stream_start_time:
            duration = datetime.now() - config.stream_start_time
            status.append(f"⏱ Uptime: {str(duration).split('.')[0]}")
    else:
        status.append("🟢 Stream: Stopped")
    
    status.append(f"🌐 RTMP URL: `{config.rtmp_url}`")
    status.append(f"📂 Videos in queue: {len(config.video_queue)}")
    
    await event.reply("\n".join(status))

@bot.on(events.NewMessage(pattern='/setrtmp'))
async def set_rtmp_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    args = event.message.text.split()
    if len(args) != 2:
        await event.reply("❌ Usage: /setrtmp rtmp_url")
        return
    
    config.rtmp_url = args[1]
    await event.reply(f"✅ RTMP URL updated to:\n`{config.rtmp_url}`")

@bot.on(events.NewMessage(pattern='/settings'))
async def settings_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    settings_text = f"""
⚙️ **Current Settings** ⚙️

Resolution: {config.stream_resolution}
Bitrate: {config.stream_bitrate}
Buffer: {config.stream_buffer}
FFmpeg preset: {config.ffmpeg_preset}
Max parallel downloads: {config.max_parallel_downloads}
Download chunk size: {config.download_chunk_size/1024}KB

To change settings, edit the config directly in the code.
"""
    await event.reply(settings_text)

# Cleanup on exit
async def cleanup():
    logger.info("Cleaning up...")
    if config.stream_process:
        await stop_stream()
    
    for video in config.video_queue:
        try:
            if os.path.exists(video['path']):
                os.remove(video['path'])
                logger.info(f"Deleted: {video['path']}")
        except Exception as e:
            logger.error(f"Error deleting {video['path']}: {e}")

def signal_handler(sig, frame):
    logger.info("Received shutdown signal")
    asyncio.run(cleanup())
    sys.exit(0)

# Main function
async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting bot...")
    try:
        await client.start()
        logger.info("Client connected")
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await cleanup()

if __name__ == '__main__':
    asyncio.run(main())
