import subprocess
import time

HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2267436984:nW65YgeqV8ToqhVO-1qDMQ"
LOGO_PATH = "logo.png"  # Make sure this exists in same folder

def start_stream():
    command = [
        "ffmpeg",
        "-re",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-analyzeduration", "5000000",
        "-probesize", "5000000",
        "-i", HLS_URL,
        "-i", LOGO_PATH,
        "-filter_complex", "overlay=W-w-10:10",  # top-right corner
        "-c:v", "libx264",  # Required when using filters
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        RTMP_URL
    ]

    while True:
        print("Starting stream with logo overlay...")
        process = subprocess.Popen(command)
        process.wait()
        print("FFmpeg stopped. Restarting...")
        time.sleep(1)

if __name__ == "__main__":
    start_stream()
