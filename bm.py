import os
import subprocess
import sys
import asyncio
import signal
from datetime import datetime
import time
# Force install required packages with --break-system-packages
required = ['telethon', 'tqdm']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Force installing {pkg} with --break-system-packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", pkg])
        except subprocess.CalledProcessError:
            print(f"Failed to install {pkg}, trying with sudo...")
            subprocess.check_call(['sudo', sys.executable, "-m", "pip", "install", "--break-system-packages", pkg])

from telethon.sync import TelegramClient, events
from telethon.tl.types import Document
from tqdm import tqdm

# Configuration
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

config = Config()

# Initialize Telegram client
client = TelegramClient(config.session_name, config.api_id, config.api_hash)
bot = TelegramClient('bot', config.api_id, config.api_hash).start(bot_token=config.bot_token)

# Progress callback for download
def progress_callback(current, total):
    bar.update(current - bar.n)

async def download_video(channel_username, message_id):
    """Download video from Telegram message"""
    try:
        msg = await client.get_messages(channel_username, ids=message_id)
        
        if msg and msg.media:
            total_size = msg.media.document.size if isinstance(msg.media, Document) else 0
            global bar
            bar = tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading')
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
            
            file_path = await client.download_media(
                msg.media, 
                file=filename, 
                progress_callback=progress_callback
            )
            bar.close()
            
            # Update config
            config.current_video_path = file_path
            config.current_message_id = message_id
            config.current_channel = channel_username
            
            return file_path
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

async def start_stream():
    """Start streaming the downloaded video smoothly with auto-restart and error logging."""
    if not config.current_video_path or not os.path.exists(config.current_video_path):
        return False, "❌ Koi video file nahi mili. Pehle /download karo."

    if config.stream_process and config.stream_process.poll() is None:
        return False, "❌ Stream already chalu hai."

    ffmpeg_command = [
        'ffmpeg',
        '-re',
        '-i', config.current_video_path,
        '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
        '-c:v', 'libx264',  # Agar GPU hai to 'h264_nvenc' kar do
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-profile:v', 'main',
        '-level', '3.1',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-minrate', '2500k',
        '-bufsize', '5000k',
        '-pix_fmt', 'yuv420p',
        '-g', '60',
        '-keyint_min', '60',
        '-x264opts', 'nal-hrd=cbr:force-cfr=1',
        '-c:a', 'aac',
        '-b:a', '160k',
        '-ar', '48000',
        '-ac', '2',
        '-async', '1',
        '-use_wallclock_as_timestamps', '1',
        '-f', 'flv',
        '-flvflags', 'no_duration_filesize',
        config.rtmp_url
    ]

    try:
        log_file = open("ffmpeg_log.txt", "w")

        config.stream_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=log_file,
            bufsize=1
        )
        config.stream_start_time = datetime.now()

        # Auto-restart check loop (optional async logic can be added)
        while True:
            time.sleep(5)  # Har 5 second mein check
            if config.stream_process.poll() is not None:
                log_file.write("❌ FFmpeg crash ho gaya, dobara start kar rahe hain...\n")
                config.stream_process = subprocess.Popen(
                    ffmpeg_command,
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=log_file,
                    bufsize=1
                )
                config.stream_start_time = datetime.now()

        return True, "✅ Stream super smooth shuru ho gayi!"
    except Exception as e:
        return False, f"❌ Stream mein dikkat: {e}"
async def stop_stream():
    """Stop the current stream"""
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

def is_user_allowed(user_id):
    """Check if user is allowed to control the bot"""
    return user_id in config.allowed_user_ids

# Bot command handlers
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not is_user_allowed(event.sender_id):
        await event.reply("🚫 You are not authorized to use this bot.")
        return
    
    help_text = """
🤖 **Telegram Stream Bot** 🤖

Available commands:
- /download [channel] [message_id] - Download video
- /startstream - Start live stream
- /stopstream - Stop live stream
- /status - Show current status
- /setrtmp [url] - Update RTMP URL
- /currentvideo - Show current video info
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
        message = await event.reply(f"⏳ Downloading video from {channel} (message {message_id})...")
        
        file_path = await download_video(channel, message_id)
        if file_path:
            await message.edit(f"✅ Video downloaded successfully!\n\n📁 Path: `{file_path}`\n\nNow you can start stream with /startstream")
        else:
            await message.edit("❌ Failed to download video. Please check:\n1. Channel username\n2. Message ID\n3. Bot has access to the channel")
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
        status.append(f"📹 Video: `{config.current_video_path}`")
        if os.path.exists(config.current_video_path):
            size = os.path.getsize(config.current_video_path) / (1024 * 1024)
            status.append(f"📦 Size: {size:.2f} MB")
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
        message = f"📹 Current video:\n`{config.current_video_path}`"
        if os.path.exists(config.current_video_path):
            size = os.path.getsize(config.current_video_path) / (1024 * 1024)
            message += f"\n📦 Size: {size:.2f} MB"
        if config.current_channel and config.current_message_id:
            message += f"\nFrom: {config.current_channel} (message {config.current_message_id})"
        await event.reply(message)
    else:
        await event.reply("ℹ️ No video currently set. Use /download first.")

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    await start_handler(event)

# Cleanup on exit
async def cleanup():
    if config.stream_process:
        config.stream_process.terminate()
        try:
            config.stream_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            config.stream_process.kill()

def signal_handler(sig, frame):
    print("\nShutting down...")
    asyncio.run(cleanup())
    sys.exit(0)

# Main function
async def main():
    # Connect client
    await client.start()
    print("Client connected.")
    
    # Start bot
    print("Bot started. Press Ctrl+C to stop.")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    client.loop.run_until_complete(main())
