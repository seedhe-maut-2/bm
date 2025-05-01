import os
import sys
import subprocess
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = "7694836384:AAE0OoYLmz1USms_ORy3Wbj1MTecQ5119Io"
CHANNEL_ID = -1002577781115
STREAM_URL = "https://starsporthindii.pages.dev/index.m3u8"

# Stream quality settings
STREAM_SETTINGS = {
    "video_size": "1280x720",
    "framerate": 30,
    "video_bitrate": "2500k",
    "audio_bitrate": "128k",
    "preset": "fast"
}

def install_ffmpeg():
    """Automatically install FFmpeg based on the operating system"""
    try:
        # Check if FFmpeg is already installed
        subprocess.run(["ffmpeg", "-version"], check=True, 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        print("🔄 FFmpeg not found. Attempting to install...")
        try:
            if sys.platform == "linux":
                # For Ubuntu/Debian
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
            elif sys.platform == "darwin":
                # For MacOS
                subprocess.run(["brew", "install", "ffmpeg"], check=True)
            elif sys.platform == "win32":
                # For Windows
                print("Please download FFmpeg from https://ffmpeg.org and add it to PATH")
                return False
            return True
        except Exception as e:
            print(f"❌ Failed to install FFmpeg: {e}")
            return False

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
                "-re",  # Read input at native frame rate
                "-i", STREAM_URL,
                "-vf", f"scale={STREAM_SETTINGS['video_size']},fps={STREAM_SETTINGS['framerate']}",
                "-c:v", "libx264",
                "-b:v", STREAM_SETTINGS["video_bitrate"],
                "-preset", STREAM_SETTINGS["preset"],
                "-c:a", "aac",
                "-b:a", STREAM_SETTINGS["audio_bitrate"],
                "-f", "flv",
                "rtmps://live.restream.io/live/YOUR_STREAM_KEY"  # Replace with your endpoint
            ]
            
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
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
    if not install_ffmpeg():
        await update.message.reply_text("❌ FFmpeg installation required. Please install FFmpeg first.")
        return
        
    manager = StreamManager()
    if await manager.start_stream():
        await update.message.reply_text("🎥 Stream started successfully!")
    else:
        await update.message.reply_text("❌ Failed to start stream. Check logs for details.")

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
        f"⚙️ Quality: {STREAM_SETTINGS['video_size']}@{STREAM_SETTINGS['framerate']}fps\n"
        f"🔗 Source: {STREAM_URL}"
    )

def main():
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        return

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    
    print("🤖 Bot is running...")
    print("Available commands: /start, /stop, /status")
    application.run_polling()

if __name__ == "__main__":
    main()
