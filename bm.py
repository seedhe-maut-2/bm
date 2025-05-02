from telethon.sync import TelegramClient
import subprocess
import os

# Telegram API credentials
api_id = 22625636  # ← यहाँ अपना API ID भरें
api_hash = 'f71778a6e1e102f33ccc4aee3b5cc697'  # ← यहाँ अपना API Hash भरें
session_name = 'stream_session'

# Telegram message link
channel_username = 'hvuvvivkvmbihlhivticutxcy'
message_id = 16

# RTMP URL (Telegram Live)
rtmp_url = 'rtmps://dc5-1.rtmp.t.me/s/2577781115:yTl41OgfjFRzupdXO1YLLQ'

# 1. Download video from Telegram
with TelegramClient(session_name, api_id, api_hash) as client:
    print("Downloading video from Telegram...")
    msg = client.get_messages(channel_username, ids=message_id)
    if msg and msg.media:
        file_path = client.download_media(msg.media, file='video.mp4')
        print(f"Downloaded to: {file_path}")
    else:
        print("Error: Video not found in the message.")
        exit()

# 2. Use FFmpeg to stream the video
print("Starting live stream to Telegram...")
ffmpeg_command = [
    'ffmpeg',
    '-re',
    '-i', 'video.mp4',
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
    rtmp_url
]

subprocess.run(ffmpeg_command)
