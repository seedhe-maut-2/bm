import os
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
                "-i", STREAM_URL,
                "-vf", f"scale={STREAM_SETTINGS['video_size']},fps={STREAM_SETTINGS['framerate']}",
                "-c:v", "libx264",
                "-b:v", STREAM_SETTINGS["video_bitrate"],
                "-preset", STREAM_SETTINGS["preset"],
                "-c:a", "aac",
                "-b:a", STREAM_SETTINGS["audio_bitrate"],
                "-f", "flv",
                "rtmps://live.restream.io/live/YOUR_STREAM_KEY"  # Replace with your RTMP endpoint
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
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None
                self.is_streaming = False
        return True

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = StreamManager()
    if await manager.start_stream():
        await update.message.reply_text("🎥 Stream started successfully!")
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
        f"Stream Status: {status_text}\n"
        f"Quality: {STREAM_SETTINGS['video_size']}@{STREAM_SETTINGS['framerate']}fps\n"
        f"Source: {STREAM_URL}"
    )

def main():
    # Check FFmpeg installation
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("❌ FFmpeg not installed! Please install FFmpeg first.")
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("Mac: brew install ffmpeg")
        print("Windows: Download from https://ffmpeg.org")
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
