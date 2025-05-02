import os
import subprocess
import sys
import asyncio
import signal
from datetime import datetime
import shutil
import math
import time
from telethon.sync import TelegramClient, events
from telethon.tl.types import Document
from tqdm import tqdm

# Force install required packages
required = ['telethon', 'tqdm']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", pkg])

class Config:
    def __init__(self):
        self.api_id = 22625636  # Replace with your API ID
        self.api_hash = 'f71778a6e1e102f33ccc4aee3b5cc697'  # Replace with your API Hash
        self.session_name = 'stream_bot_session'
        self.bot_token = '7710269508:AAGTZlpf_GBpwh2kILwUjzE6gys4EgdYmDk'  # Replace with your bot token
        self.allowed_user_ids = [8167507955]  # Replace with your user ID
        self.current_video_path = None
        self.current_message_id = None
        self.current_channel = None
        self.rtmp_url = 'rtmps://dc5-1.rtmp.t.me/s/2577781115:yTl41OgfjFRzupdXO1YLLQ'
        self.stream_process = None
        self.stream_start_time = None
        self.download_progress_message = None
        self.last_progress_update = 0

config = Config()
client = TelegramClient(config.session_name, config.api_id, config.api_hash)
bot = TelegramClient('bot', config.api_id, config.api_hash).start(bot_token=config.bot_token)

# Helper functions
def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_storage_info():
    total, used, free = shutil.disk_usage("/")
    return {
        'total': format_size(total),
        'used': format_size(used),
        'free': format_size(free),
        'percent_used': round((used / total) * 100, 2)
    }

async def progress_callback(current, total):
    global bar
    progress = current / total * 100
    bar.update(current - bar.n)
    
    # Throttle updates to once per 2 seconds
    now = time.time()
    if now - config.last_progress_update > 2 and config.download_progress_message:
        try:
            elapsed = bar.format_dict['elapsed']
            rate = bar.format_dict['rate'] if bar.format_dict['rate'] else 0
            remaining = (total - current) / rate if rate > 0 else 0
            
            await config.download_progress_message.edit(
                f"📥 Downloading...\n"
                f"📁 {os.path.basename(config.current_video_path)}\n"
                f"🔽 {format_size(current)} / {format_size(total)}\n"
                f"📊 {progress:.2f}%\n"
                f"⚡ {format_size(rate)}/s\n"
                f"⏱ {elapsed:.1f}s | ⏳ {remaining:.1f}s remaining"
            )
            config.last_progress_update = now
        except Exception as e:
            print(f"Progress update error: {e}")

def is_user_allowed(user_id):
    return user_id in config.allowed_user_ids

async def download_video(channel_username, message_id, event):
    try:
        # Convert message_id to integer
        try:
            message_id = int(message_id)
        except ValueError:
            await event.reply("❌ Message ID must be a number")
            return None

        msg = await client.get_messages(channel_username, ids=message_id)
        
        if msg is None:
            await event.reply("❌ Message not found. Check if the bot has access to the channel.")
            return None
            
        if not msg.media:
            await event.reply("❌ The specified message doesn't contain any media")
            return None

        if not isinstance(msg.media, Document):
            await event.reply("❌ The media is not a downloadable file")
            return None

        total_size = msg.media.document.size
        global bar
        bar = tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
        config.current_video_path = filename
        
        config.download_progress_message = await event.reply(
            f"⏳ Starting download...\n"
            f"📁 {filename}\n"
            f"📦 Size: {format_size(total_size)}\n"
            f"📊 0% (0/{format_size(total_size)})"
        )
        config.last_progress_update = time.time()
        
        file_path = await client.download_media(
            msg.media, 
            file=filename, 
            progress_callback=progress_callback
        )
        bar.close()
        
        config.current_video_path = file_path
        config.current_message_id = message_id
        config.current_channel = channel_username
        
        await config.download_progress_message.edit(
            f"✅ Download complete!\n"
            f"📁 {os.path.basename(file_path)}\n"
            f"📦 {format_size(os.path.getsize(file_path))}\n"
            f"⏱ {bar.format_dict['elapsed']:.1f}s\n"
            f"⚡ Avg: {format_size(bar.format_dict['rate'])}/s"
        )
        config.download_progress_message = None
        return file_path

    except Exception as e:
        if config.download_progress_message:
            await config.download_progress_message.edit(f"❌ Download failed: {str(e)}")
        config.download_progress_message = None
        return None

async def start_stream():
    if not config.current_video_path or not os.path.exists(config.current_video_path):
        return False, "❌ No video file available. Please download first using /download."
    
    if config.stream_process and config.stream_process.poll() is None:
        return False, "❌ Stream is already running."
    
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-re',
            '-i', config.current_video_path,
            '-vf', 'scale=1280:720',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-maxrate', '3000k',
            '-bufsize', '6000k',
            '-pix_fmt', 'yuv420p',
            '-g', '50',
            '-c:a', 'aac',
            '-b:a', '160k',
            '-ar', '44100',
            '-f', 'flv',
            config.rtmp_url
        ]
        
        config.stream_process = subprocess.Popen(
            ffmpeg_command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )
        config.stream_start_time = datetime.now()
        return True, "✅ Stream started successfully!"
    except Exception as e:
        return False, f"❌ Stream error: {e}"

async def stop_stream():
    if config.stream_process:
        config.stream_process.terminate()
        try:
            config.stream_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            config.stream_process.kill()
        
        stream_duration = datetime.now() - config.stream_start_time if config.stream_start_time else None
        config.stream_process = None
        config.stream_start_time = None
        
        message = "✅ Stream stopped."
        if stream_duration:
            message += f"\n⏱ Duration: {str(stream_duration).split('.')[0]}"
        return True, message
    return False, "❌ No active stream to stop."

async def delete_all_videos():
    deleted_files = []
    total_size = 0
    for filename in os.listdir('.'):
        if filename.startswith('video_') and filename.endswith('.mp4'):
            try:
                file_size = os.path.getsize(filename)
                os.remove(filename)
                deleted_files.append(f"✅ {filename} ({format_size(file_size)})")
                total_size += file_size
            except Exception as e:
                deleted_files.append(f"❌ {filename} (failed: {str(e)})")
    
    # Reset current video if it was deleted
    if (config.current_video_path and 
        not os.path.exists(config.current_video_path)):
        config.current_video_path = None
        config.current_message_id = None
        config.current_channel = None
    
    return deleted_files, total_size

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    help_text = """
🤖 **Telegram Stream Bot** 🤖

📥 Video Commands:
- /download [channel] [msg_id] - Download video
- /currentvideo - Show current video
- /cleanstorage - Delete all videos

📺 Stream Commands:
- /startstream - Start streaming
- /stopstream - Stop streaming
- /status - Stream status

⚙️ Config Commands:
- /setrtmp [url] - Change RTMP URL
- /storage - Show disk space

ℹ️ Help:
- /help - Show this menu
"""
    await event.reply(help_text)

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    await start_handler(event)

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
        message_id = args[2]
        await download_video(channel, message_id, event)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/startstream'))
async def start_stream_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    message = await event.reply("🔄 Starting stream...")
    success, result = await start_stream()
    await message.edit(result)

@bot.on(events.NewMessage(pattern='/stopstream'))
async def stop_stream_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    message = await event.reply("🔄 Stopping stream...")
    success, result = await stop_stream()
    await message.edit(result)

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    status = []
    status.append("📊 **Current Status**")
    
    if config.current_video_path:
        status.append(f"📹 Video: `{os.path.basename(config.current_video_path)}`")
        if os.path.exists(config.current_video_path):
            status.append(f"📦 Size: {format_size(os.path.getsize(config.current_video_path))}")
        else:
            status.append("❌ File missing")
    
    if config.current_channel and config.current_message_id:
        status.append(f"📩 Source: {config.current_channel} (message {config.current_message_id})")
    
    if config.stream_process and config.stream_process.poll() is None:
        status.append("🔴 Stream: Running")
        if config.stream_start_time:
            duration = datetime.now() - config.stream_start_time
            status.append(f"⏱ Uptime: {str(duration).split('.')[0]}")
    else:
        status.append("🟢 Stream: Stopped")
    
    status.append(f"🌐 RTMP URL: `{config.rtmp_url}`")
    
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

@bot.on(events.NewMessage(pattern='/currentvideo'))
async def current_video_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    if config.current_video_path:
        message = f"📹 Current video:\n`{os.path.basename(config.current_video_path)}`"
        if os.path.exists(config.current_video_path):
            message += f"\n📦 Size: {format_size(os.path.getsize(config.current_video_path))}"
        if config.current_channel and config.current_message_id:
            message += f"\nFrom: {config.current_channel} (message {config.current_message_id})"
        await event.reply(message)
    else:
        await event.reply("ℹ️ No video currently set. Use /download first.")

@bot.on(events.NewMessage(pattern='/cleanstorage'))
async def clean_storage_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    message = await event.reply("🧹 Cleaning storage...")
    deleted_files, total_size = await delete_all_videos()
    storage = get_storage_info()
    
    response = [
        "🗑 Deleted files:",
        *deleted_files[:10],  # Show first 10 files to avoid message too long
        f"\n💾 Total freed: {format_size(total_size)}",
        f"\n📊 Storage status:",
        f"Total: {storage['total']}",
        f"Used: {storage['used']} ({storage['percent_used']}%)",
        f"Free: {storage['free']}"
    ]
    
    await message.edit("\n".join(response))

@bot.on(events.NewMessage(pattern='/storage'))
async def storage_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    storage = get_storage_info()
    response = (
        "💾 Storage Information:\n"
        f"Total: {storage['total']}\n"
        f"Used: {storage['used']} ({storage['percent_used']}%)\n"
        f"Free: {storage['free']}"
    )
    await event.reply(response)

async def cleanup():
    if config.stream_process:
        config.stream_process.terminate()
        try:
            config.stream_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            config.stream_process.kill()
    if config.download_progress_message:
        try:
            await config.download_progress_message.delete()
        except:
            pass

def signal_handler(sig, frame):
    print("\nShutting down...")
    asyncio.run(cleanup())
    sys.exit(0)

async def main():
    await client.start()
    print("Client connected.")
    print("Bot started. Press Ctrl+C to stop.")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    client.loop.run_until_complete(main())
