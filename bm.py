import subprocess
import time
import threading

HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2267436984:nW65YgeqV8ToqhVO-1qDMQ"

def run_ffmpeg():
    command = [
        "ffmpeg",
        "-re",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-strict", "experimental",
        "-analyzeduration", "5000000",
        "-probesize", "5000000",
        "-rw_timeout", "5000000",
        "-timeout", "5000000",
        "-i", HLS_URL,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        RTMP_URL
    ]
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def monitor_stream():
    while True:
        print("Launching FFmpeg stream...")
        process = run_ffmpeg()
        start_time = time.time()
        while True:
            if process.poll() is not None:
                print("FFmpeg crashed. Restarting...")
                break
            # Check every second if process is alive
            time.sleep(1)

if __name__ == "__main__":
    try:
        monitor_stream()
    except KeyboardInterrupt:
        print("Streaming manually stopped.")
