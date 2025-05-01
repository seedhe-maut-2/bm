import os
import sys
import subprocess
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types.input_stream import InputAudioStream, InputVideoStream

# ---- Auto Dependency Installer ----
def install_dependencies():
    required_packages = {
        'python-telegram-bot': '20.0',
        'pytgcalls': '',
        'ffmpeg-python': ''
    }
    
    print("🔍 Checking dependencies...")
    for package, version in required_packages.items():
        try:
            __import__(package.split('==')[0])
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"⚠️ Installing {package}...")
            install_cmd = [sys.executable, "-m", "pip", "install", f"{package}{'=='+version if version else ''}"]
            subprocess.check_call(install_cmd, stdout=subprocess.DEVNULL)

install_dependencies()

# ---- Configuration ----
BOT_TOKEN = "7694836384:AAE0OoYLmz1USms_ORy3Wbj1MTecQ5119Io"  # Replace with your bot token
CHANNEL_ID = -1002577781115   # Replace with your channel ID (must be negative)
STREAM_URL = "https://starsporthindii.pages.dev/index.m3u8"

# ---- Optimized Stream Parameters ----
STREAM_CONFIG = {
    "video": InputVideoStream(
        fps=30,
        resolution=(1280, 720),
        bitrate=2500000,
        minimum_fps=25,
        maximum_fps=30
    ),
    "audio": InputAudioStream(
        bitrate=128000,
        sample_rate=48000,
        channels=2
    ),
    "buffer_time": 5,
    "timeout": 30,
    "reconnect_delay": 5,
    "max_retries": 3
}

# ---- Initialize PyTgCalls ----
pytgcalls = PyTgCalls()

# ---- Stream Management ----
class StreamManager:
    _instance = None
    is_streaming = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def start_stream(self, max_retries=3):
        retry_count = 0
        while retry_count < max_retries:
            try:
                if self.is_streaming:
                    await pytgcalls.leave_group_call(CHANNEL_ID)
                
                await pytgcalls.join_group_call(
                    CHANNEL_ID,
                    MediaStream(
                        STREAM_URL,
                        video_parameters=STREAM_CONFIG["video"],
                        audio_parameters=STREAM_CONFIG["audio"],
                        buffer_time=STREAM_CONFIG["buffer_time"],
                        timeout=STREAM_CONFIG["timeout"],
                        reconnect_delay=STREAM_CONFIG["reconnect_delay"]
                    ),
                )
                self.is_streaming = True
                return True
            except Exception as e:
                retry_count += 1
                print(f"Attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(5)
        
        self.is_streaming = False
        return False

    async def stop_stream(self):
        try:
            await pytgcalls.leave_group_call(CHANNEL_ID)
            self.is_streaming = False
            return True
        except Exception as e:
            print(f"Error stopping stream: {str(e)}")
            return False

# ---- Telegram Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    await update.message.reply_text("🔄 Starting high-quality stable stream...")
    
    if await manager.start_stream(STREAM_CONFIG["max_retries"]):
        await update.message.reply_text("🎥 Stream started with HD quality!")
    else:
        await update.message.reply_text("❌ Failed to start stream after multiple attempts")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    if await manager.stop_stream():
        await update.message.reply_text("⏹ Stream stopped successfully!")
    else:
        await update.message.reply_text("⚠️ Error stopping stream (may have already stopped)")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    status_text = "🟢 LIVE now!" if manager.is_streaming else "🔴 Offline"
    quality = f"{STREAM_CONFIG['video'].resolution[0]}p@{STREAM_CONFIG['video'].fps}fps"
    await update.message.reply_text(
        f"📊 Stream Status: {status_text}\n"
        f"🎚 Quality: {quality}\n"
        f"🔗 Source: {STREAM_URL}"
    )

# ---- Main Application ----
def main():
    # Check FFmpeg installation
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("❌ FFmpeg not installed! Please install FFmpeg first.")
        print("On Ubuntu/Debian: sudo apt install ffmpeg")
        print("On Mac: brew install ffmpeg")
        print("On Windows: Download from https://ffmpeg.org")
        return

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    
    # Start PyTgCalls
    pytgcalls.start()
    
    print("🤖 Bot is running...")
    print(f"🔗 Stream URL: {STREAM_URL}")
    print("Available commands:")
    print("/start - Start the stream")
    print("/stop - Stop the stream")
    print("/status - Check stream status")
    
    application.run_polling()

if __name__ == "__main__":
    main()
