import subprocess

# HLS source
HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"

# Full RTMPS URL (from Telegram)
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2440538814:kDLjt9MP0sRKSFhD4bS6SQ"

# FFmpeg command
command = [
    "ffmpeg",
    "-re",                     # Stream in real time
    "-i", HLS_URL,             # Input .m3u8 URL
    "-c:v", "copy",            # Copy video stream without re-encoding
    "-c:a", "aac",             # Encode audio as AAC
    "-f", "flv",               # Format for RTMP streaming
    RTMP_URL
]

# Run the command
subprocess.run(command)
