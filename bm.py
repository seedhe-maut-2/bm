import requests
import time

def send_safe_request():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Educational-Test)",
            "X-Forwarded-For": f"127.0.0.{random.randint(1, 100)}",
            "Test-Header": "Hello"
        }
        response = requests.get("https://httpbin.org/get", headers=headers, timeout=5)
        
        # रिस्पॉन्स चेक करें
        print(f"[✅] Status: {response.status_code}")
        print(f"[ℹ️] Your IP (as per httpbin): {response.json().get('origin')}")
        print(f"[ℹ️] Headers Received: {response.json().get('headers')}")
        
    except Exception as e:
        print(f"[❌] Error: {e}")

# धीमी और सेफ टेस्टिंग (5 रिक्वेस्ट्स, 2 सेकंड के अंतराल के साथ)
for _ in range(5):
    send_safe_request()
    time.sleep(2)  # 2 सेकंड का डिले (Rate Limiting से बचने के लिए)
