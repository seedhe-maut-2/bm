import os
import subprocess
import sys

# Auto-install required modules
required = ['telethon', 'tqdm']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from telethon.sync import TelegramClient
from telethon.tl.types import Document
from tqdm import tqdm

# Telegram API credentials
api_id = 22625636  # ← Your API ID
api_hash = 'f71778a6e1e102f33ccc4aee3b5cc697'  # ← Your API Hash
session_name = 'stream_session'

# Telegram message details
channel_username = 'hvuvvivkvmbihlhivticutxcy'
message_id = 20

# RTMP stream URL
rtmp_url = 'rtmps://dc5-1.rtmp.t.me/s/2577781115:yTl41OgfjFRzupdXO1YLLQ'

# Progress callback for download
def progress_callback(current, total):
    bar.update(current - bar.n)

# 1. Download video from Telegram
with TelegramClient(session_name, api_id, api_hash) as client:
    print("Connecting to Telegram...")
    msg = client.get_messages(channel_username, ids=message_id)

    if msg and msg.media:
        total_size = msg.media.document.size if isinstance(msg.media, Document) else 0
        bar = tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading')
        file_path = client.download_media(msg.media, file='video.mp4', progress_callback=progress_callback)
        bar.close()
        print(f"Downloaded to: {file_path}")
    else:
        print("Error: Could not find the video.")
        sys.exit()

# 2. Stream to Telegram using FFmpeg
print("\nStarting live stream to Telegram...")

ffmpeg_command = [
    'ffmpeg',
    '-re',
    '-i', 'video.mp4',
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
    rtmp_url
]

process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

# Streaming progress bar (simulated)
bar2 = tqdm(total=100, desc='Streaming', bar_format="{l_bar}{bar} | {elapsed}", dynamic_ncols=True)
try:
    while True:
        line = process.stdout.readline()
        if not line:
            break
        if "frame=" in line:
            bar2.update(1)
        if process.poll() is not None:
            break
except KeyboardInterrupt:
    process.terminate()
    print("\nStream interrupted.")
bar2.close()
print("Live stream finished.")
