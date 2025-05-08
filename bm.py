import subprocess
import time
import os

HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2267436984:nW65YgeqV8ToqhVO-1qDMQ"
LOGO_PATH = "logo.png"  # Place your logo image here

def run_ffmpeg():
    command = [
        "ffmpeg",
        "-loglevel", "error",                # only log errors
        "-re",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-analyzeduration", "5000000",
        "-probesize", "5000000",
        "-rw_timeout", "10000000",
        "-timeout", "10000000",
        "-i", HLS_URL,
        "-i", LOGO_PATH,
        "-filter_complex", "overlay=W-w-10:10",  # logo top-right
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-c:a", "aac",
        "-b:a", "128k",
        "-bufsize", "1000k",
        "-maxrate", "1000k",
        "-f", "flv",
        RTMP_URL
    ]
    return subprocess.Popen(command)

def monitor_stream():
    while True:
        print("Launching ultra-smooth stream with logo...")
        process = run_ffmpeg()
        while True:
            if process.poll() is not None:
                print("Stream crashed. Restarting immediately...")
                break
            time.sleep(0.5)  # quicker monitor

if __name__ == "__main__":
    if not os.path.exists(LOGO_PATH):
        print(f"Logo file not found: {LOGO_PATH}")
    else:
        try:
            monitor_stream()
        except KeyboardInterrupt:
            print("Streaming manually stopped.")
