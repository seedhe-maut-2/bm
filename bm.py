import os
import sys
import subprocess
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = "7694836384:AAE0OoYLmz1USms_ORy3Wbj1MTecQ5119Io"
CHANNEL_ID = -1002577781115  # Your channel ID (must be negative)
STREAM_URL = "https://starsporthindii.pages.dev/index.m3u8"

# Stream quality settings
STREAM_SETTINGS = {
    "video_size": "1280x720",
    "framerate": 30,
    "video_bitrate": "2500k",
    "audio_bitrate": "128k",
    "preset": "fast"
}

def check_dependencies():
    """Check and install required dependencies"""
    try:
        import python_telegram_bot
    except ImportError:
        print("Installing python-telegram-bot...")
        subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.0"], check=True)
    
    # FFmpeg check
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("FFmpeg not found. Attempting to install...")
        try:
            if sys.platform == "linux":
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
            elif sys.platform == "darwin":
                subprocess.run(["brew", "install", "ffmpeg"], check=True)
            else:
                print("Please install FFmpeg manually on Windows")
                return False
        except Exception as e:
            print(f"Failed to install FFmpeg: {e}")
            return False
    return True

class StreamManager:
    def __init__(self):
        self.process = None
        self.is_streaming = False

    async def start_stream(self):
        if self.is_streaming:
            return True

        try:
            ffmpeg_cmd = [
                "ffmpeg",
                "-re",  # Real-time streaming
                "-i", STREAM_URL,
                "-vf", f"scale={STREAM_SETTINGS['video_size']},fps={STREAM_SETTINGS['framerate']}",
                "-c:v", "libx264",
                "-b:v", STREAM_SETTINGS["video_bitrate"],
                "-preset", STREAM_SETTINGS["preset"],
                "-c:a", "aac",
                "-b:a", STREAM_SETTINGS["audio_bitrate"],
                "-f", "mpegts",  # MPEG-TS format works best with Telegram
                "pipe:1"  # Output to stdout
            ]
            
            # Start FFmpeg process
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8  # Large buffer for smooth streaming
            )
            self.is_streaming = True
            return True
        except Exception as e:
            print(f"Stream start error: {e}")
            return False

    async def stop_stream(self):
        if self.process and self.is_streaming:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception as e:
                print(f"Error stopping stream: {e}")
            finally:
                self.process = None
                self.is_streaming = False
        return True

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_dependencies():
        await update.message.reply_text("❌ Required dependencies not installed")
        return
        
    manager = StreamManager()
    if await manager.start_stream():
        # Send the stream to Telegram
        try:
            with open('stream.ts', 'wb') as f:
                while manager.is_streaming and manager.process.poll() is None:
                    data = manager.process.stdout.read(1024)
                    if not data:
                        break
                    f.write(data)
            
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=open('stream.ts', 'rb'),
                supports_streaming=True,
                timeout=9999
            )
            await update.message.reply_text("🎥 Stream started successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Streaming error: {e}")
            await manager.stop_stream()
    else:
        await update.message.reply_text("❌ Failed to start stream")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    if await manager.stop_stream():
        await update.message.reply_text("⏹ Stream stopped successfully!")
    else:
        await update.message.reply_text("⚠️ No active stream to stop")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    status_text = "🟢 LIVE" if manager.is_streaming else "🔴 OFFLINE"
    await update.message.reply_text(
        f"📺 Stream Status: {status_text}\n"
        f"⚙️ Quality: {STREAM_SETTINGS['video_size']}@{STREAM_SETTINGS['framerate']}fps"
    )

def main():
    if not check_dependencies():
        print("❌ Required dependencies not installed")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
