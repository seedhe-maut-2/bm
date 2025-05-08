import subprocess
import logging

HLS_URL = "https://starsportshindiii.pages.dev/index.m3u8"
RTMP_URL = "rtmps://dc5-1.rtmp.t.me/s/2267436984:nW65YgeqV8ToqhVO-1qDMQ"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_stream():
    command = [
        "ffmpeg",
        "-re",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-analyzeduration", "5000000",
        "-probesize", "5000000",
        "-i", HLS_URL,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-bufsize", "512k",
        "-maxrate", "1000k",
        "-preset", "veryfast",
        "-threads", "2",
        "-f", "flv",
        RTMP_URL
    ]
    
    while True:
        try:
            logging.info("Starting stream...")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            logging.warning("Stream ended or crashed. Restarting immediately...")
            logging.debug(stderr.decode())
        except Exception as e:
            logging.error(f"Streaming error: {e}")

if __name__ == "__main__":
    start_stream()
