import subprocess
import time

HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2267436984:nW65YgeqV8ToqhVO-1qDMQ"

def start_stream():
    command = [
        "ffmpeg",
        "-re",                           # Real-time input
        "-fflags", "nobuffer",          # Lower latency
        "-flags", "low_delay",          
        "-analyzeduration", "10000000", # Increase analysis for better sync
        "-probesize", "10000000",
        "-i", HLS_URL,
        "-c:v", "copy",                 # No video re-encoding
        "-c:a", "aac",                  # Encode audio
        "-b:a", "128k",                 # Stable audio bitrate
        "-f", "flv",                    # FLV format for RTMP
        RTMP_URL
    ]
    
    while True:
        print("Starting stream...")
        process = subprocess.Popen(command)
        process.wait()  # Wait until process exits
        print("Stream crashed or ended. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    start_stream()
