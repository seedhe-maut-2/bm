import os
import time
import uuid
import string
import random
import requests
import webbrowser
from colorama import init, Fore, Style
from datetime import datetime
import base64

# Initialize colorama
init()

# Check and install required modules
required_modules = {
    'termcolor': 'termcolor',
    'names': 'names',
    'requests': 'requests',
    'cfonts': 'python-cfonts',
    'pyfiglet': 'pyfiglet',
    'pillow': 'pillow'
}

for module, package in required_modules.items():
    try:
        __import__(module)
    except ImportError:
        os.system(f'pip install {package}')

import termcolor
import names
from cfonts import render
import pyfiglet
from PIL import Image
import io

# Configuration
PROXIES = None  # You can add proxies here if needed
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # seconds
DEFAULT_APP_ID = '936619743392459'  # Fallback Instagram app ID

# Profile and post images (base64 encoded sample images)
PROFILE_IMAGE_URL = "https://t.me/gggkkkggggiii/65"
POST_IMAGE_URLS = [
    "https://t.me/gggkkkggggiii/68",
    "https://t.me/gggkkkggggiii/66",
    "https://t.me/gggkkkggggiii/67"
]

class InstagramAccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.user_agent = self.generate_user_agent()
        self.headers = None
        self.cookies = None
        self.device_id = None
        
    def generate_user_agent(self):
        """Generate a random mobile user agent"""
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = f"{random.randint(100, 115)}.0.0.0"
        return f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36'

    def get_headers(self, country='US', language='en'):
        """Get Instagram headers with necessary cookies"""
        for _ in range(MAX_RETRIES):
            try:
                # Initial request to get cookies with a generic user agent
                temp_headers = {
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Get Instagram cookies first
                self.session.headers.update(temp_headers)
                ig_response = self.session.get(
                    'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                    timeout=30
                )
                
                # Generate device ID if not exists
                if not hasattr(self, 'device_id'):
                    self.device_id = f"android-{str(uuid.uuid4())[:16]}"
                
                # Extract cookies
                self.cookies = {
                    'csrftoken': ig_response.cookies.get('csrftoken', ''),
                    'mid': ig_response.cookies.get('mid', ''),
                    'ig_nrcb': '1',
                    'ig_did': ig_response.cookies.get('ig_did', str(uuid.uuid4())),
                    'datr': str(uuid.uuid4()).replace('-', '')[:20],
                }
                
                # Build cookie string
                cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
                
                # Final headers
                self.headers = {
                    'authority': 'www.instagram.com',
                    'accept': '*/*',
                    'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': cookie_str,
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/accounts/signup/email/',
                    'sec-ch-prefers-color-scheme': 'light',
                    'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'user-agent': self.user_agent,
                    'x-asbd-id': '198387',
                    'x-csrftoken': self.cookies['csrftoken'],
                    'x-ig-app-id': DEFAULT_APP_ID,
                    'x-ig-www-claim': '0',
                    'x-instagram-ajax': '1',
                    'x-requested-with': 'XMLHttpRequest',
                    'x-web-device-id': self.cookies['ig_did'],
                }
                
                return self.headers
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error getting headers: {e}{Style.RESET_ALL}")
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return None

    def get_username_suggestions(self, name, email):
        """Get username suggestions from Instagram"""
        for _ in range(MAX_RETRIES):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/birthday/'
                
                data = {
                    'email': email,
                    'name': name + str(random.randint(1, 99)),
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200 and 'suggestions' in response.json():
                    return random.choice(response.json()['suggestions'])
                else:
                    print(f"{Fore.YELLOW}Username suggestions error: {response.text}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.YELLOW}Error getting username suggestions: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # If all attempts fail, generate a random username
        return f"{name.lower()}{random.randint(100, 999)}"

    def send_verification_email(self, email):
        """Send verification email to the provided address"""
        for _ in range(MAX_RETRIES):
            try:
                data = {
                    'device_id': self.device_id,
                    'email': email,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/send_verify_email/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )
                
                return response.json()
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error sending verification email: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return {'status': 'fail', 'message': 'Failed to send verification email'}

    def verify_confirmation_code(self, email, code):
        """Verify the confirmation code received via email"""
        for _ in range(MAX_RETRIES):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/emailConfirmation/'
                
                data = {
                    'code': code,
                    'device_id': self.device_id,
                    'email': email,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/check_confirmation_code/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                return response.json()
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error verifying confirmation code: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return {'status': 'fail', 'message': 'Failed to verify confirmation code'}

    def create_account(self, email, signup_code):
        """Create the Instagram account with the verified email"""
        for _ in range(MAX_RETRIES):
            try:
                firstname = names.get_first_name()
                username = self.get_username_suggestions(firstname, email)
                password = f"{firstname.strip()}@{random.randint(111, 999)}"
                
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/username/'
                
                data = {
                    'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{password}',
                    'email': email,
                    'username': username,
                    'first_name': firstname,
                    'month': random.randint(1, 12),
                    'day': random.randint(1, 28),
                    'year': random.randint(1990, 2001),
                    'client_id': self.device_id,
                    'seamless_login_enabled': '1',
                    'tos_version': 'row',
                    'force_sign_up_code': signup_code,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                try:
                    result = response.json()
                except ValueError:
                    print(f"{Fore.RED}Invalid JSON response: {response.text}{Style.RESET_ALL}")
                    continue
                
                if result.get('account_created', False):
                    account_info = {
                        'username': username,
                        'password': password,
                        'email': email,
                        'cookies': dict(response.cookies),
                        'headers': self.headers,
                        'creation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': result.get('user_id', ''),
                        'session_id': response.cookies.get('sessionid', '')
                    }
                    
                    # Set profile picture and make posts
                    if account_info['user_id']:
                        self.set_profile_picture(account_info)
                        self.make_initial_posts(account_info)
                    
                    return account_info
                else:
                    print(f"{Fore.YELLOW}Account creation failed: {response.text}{Style.RESET_ALL}")
                    if 'errors' in result:
                        error_msg = result['errors']
                        if isinstance(error_msg, dict) and 'email' in error_msg:
                            if any(e.get('code') == 'email_is_taken' for e in error_msg['email']):
                                print(f"{Fore.RED}This email is already registered with Instagram{Style.RESET_ALL}")
                                return None
                        print(f"{Fore.RED}Error details: {error_msg}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}Error creating account: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return None

    def download_image(self, url):
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"{Fore.YELLOW}Error downloading image: {e}{Style.RESET_ALL}")
        return None

    def set_profile_picture(self, account_info):
        """Set profile picture for the new account"""
        print(Fore.CYAN + "[*] Setting profile picture..." + Style.RESET_ALL)
        
        # Download profile image
        image_data = self.download_image(PROFILE_IMAGE_URL)
        if not image_data:
            print(Fore.RED + "[-] Failed to download profile image" + Style.RESET_ALL)
            return False
        
        try:
            # Prepare the image upload
            upload_url = "https://www.instagram.com/api/v1/web/accounts/web_change_profile_picture/"
            
            files = {
                'profile_pic': ('profile_pic.jpg', image_data, 'image/jpeg')
            }
            
            headers = account_info['headers'].copy()
            headers['referer'] = 'https://www.instagram.com/accounts/edit/'
            headers['x-csrftoken'] = account_info['cookies'].get('csrftoken', '')
            
            response = self.session.post(
                upload_url,
                headers=headers,
                files=files,
                cookies=account_info['cookies'],
                timeout=30
            )
            
            if response.status_code == 200:
                print(Fore.GREEN + "[+] Profile picture set successfully" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + f"[-] Failed to set profile picture: {response.text}" + Style.RESET_ALL)
                return False
                
        except Exception as e:
            print(Fore.RED + f"[-] Error setting profile picture: {e}" + Style.RESET_ALL)
            return False

    def make_initial_posts(self, account_info):
        """Make initial posts to make account look genuine"""
        print(Fore.CYAN + "[*] Creating initial posts..." + Style.RESET_ALL)
        
        for i, post_url in enumerate(POST_IMAGE_URLS[:2]):  # Post first 2 images only
            # Download post image
            image_data = self.download_image(post_url)
            if not image_data:
                print(Fore.RED + f"[-] Failed to download post image {i+1}" + Style.RESET_ALL)
                continue
            
            try:
                # Upload the image
                upload_url = "https://www.instagram.com/api/v1/media/upload/"
                
                files = {
                    'file': ('post_image.jpg', image_data, 'image/jpeg')
                }
                
                headers = account_info['headers'].copy()
                headers['referer'] = 'https://www.instagram.com/'
                headers['x-csrftoken'] = account_info['cookies'].get('csrftoken', '')
                
                # First upload the image
                upload_response = self.session.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    cookies=account_info['cookies'],
                    timeout=30
                )
                
                if upload_response.status_code != 200:
                    print(Fore.RED + f"[-] Failed to upload post image {i+1}: {upload_response.text}" + Style.RESET_ALL)
                    continue
                
                upload_data = upload_response.json()
                upload_id = upload_data.get('upload_id')
                
                if not upload_id:
                    print(Fore.RED + f"[-] No upload ID received for post {i+1}" + Style.RESET_ALL)
                    continue
                
                # Configure the post
                configure_url = "https://www.instagram.com/api/v1/media/configure/"
                
                caption = random.choice([
                    "Enjoying the day! 😊",
                    "Beautiful moments ✨",
                    "Life is good 🌞",
                    "Making memories 📸",
                    "Happy days! 🎉"
                ])
                
                configure_data = {
                    'upload_id': upload_id,
                    'caption': caption,
                    'usertags': '',
                    'custom_accessibility_caption': '',
                    'retry_timeout': ''
                }
                
                configure_response = self.session.post(
                    configure_url,
                    headers=headers,
                    data=configure_data,
                    cookies=account_info['cookies'],
                    timeout=30
                )
                
                if configure_response.status_code == 200:
                    print(Fore.GREEN + f"[+] Post {i+1} created successfully" + Style.RESET_ALL)
                else:
                    print(Fore.RED + f"[-] Failed to configure post {i+1}: {configure_response.text}" + Style.RESET_ALL)
                    
            except Exception as e:
                print(Fore.RED + f"[-] Error creating post {i+1}: {e}" + Style.RESET_ALL)

    def generate_session_id(self, username, password):
        """Generate session ID for the account"""
        try:
            login_url = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"
            
            data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false'
            }
            
            response = self.session.post(
                login_url,
                headers=self.headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200 and response.json().get('authenticated'):
                return response.cookies.get('sessionid')
            else:
                print(Fore.RED + f"[-] Failed to generate session ID: {response.text}" + Style.RESET_ALL)
                return None
                
        except Exception as e:
            print(Fore.RED + f"[-] Error generating session ID: {e}" + Style.RESET_ALL)
            return None

def display_banner():
    """Display the tool banner"""
    fonts = ['small']
    colors = [Fore.GREEN]

    for font in fonts:
        f = pyfiglet.Figlet(font=font)
        for color in colors:
            output = f.renderText('INSTA CREATOR')
            print(color + output + Style.RESET_ALL)
        
    print(Fore.YELLOW + "~ Instagram Account Creator ~" + Style.RESET_ALL)
    print(Fore.YELLOW + "~ For educational purposes only ~" + Style.RESET_ALL)
    print(Fore.RED + "________________________________________________________" + Style.RESET_ALL)

def generate_temp_email():
    """Generate a temporary email address"""
    domains = ["hi2.in", "mailinator.com", "tempmail.com", "10minutemail.com"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{username}@{domain}"

def main():
    display_banner()
    

    
    creator = InstagramAccountCreator()
    
    try:
        # Get headers first
        print(Fore.CYAN + "[*] Initializing session..." + Style.RESET_ALL)
        headers = creator.get_headers()
        
        if not headers:
            print(Fore.RED + "[-] Failed to initialize session" + Style.RESET_ALL)
            return
        
        # Get email from user
        email = input(Fore.GREEN + "[?] Enter your email: " + Style.RESET_ALL).strip()
        
        # Send verification email
        print(Fore.CYAN + "[*] Sending verification email..." + Style.RESET_ALL)
        send_result = creator.send_verification_email(email)
        
        if send_result.get('email_sent', False):
            # Get verification code from user
            code = input(Fore.GREEN + "[?] Enter the verification code: " + Style.RESET_ALL).strip()
            
            # Verify code
            print(Fore.CYAN + "[*] Verifying code..." + Style.RESET_ALL)
            verify_result = creator.verify_confirmation_code(email, code)
            
            if verify_result.get('status') == 'ok':
                signup_code = verify_result.get('signup_code')
                
                # Create account
                print(Fore.CYAN + "[*] Creating account..." + Style.RESET_ALL)
                account_info = creator.create_account(email, signup_code)
                
                if account_info:
                    print(Fore.GREEN + "\n[+] Account created successfully!" + Style.RESET_ALL)
                    print(Fore.YELLOW + "="*50 + Style.RESET_ALL)
                    print(Fore.CYAN + f"Username: {account_info['username']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Password: {account_info['password']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Email: {account_info['email']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"User ID: {account_info['user_id']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Session ID: {account_info['session_id']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Created at: {account_info['creation_time']}" + Style.RESET_ALL)
                    print(Fore.YELLOW + "="*50 + Style.RESET_ALL)
                    
                    # Save account info to file
                    try:
                        with open('instagram_accounts.txt', 'a') as f:
                            f.write(f"Username: {account_info['username']}\n")
                            f.write(f"Password: {account_info['password']}\n")
                            f.write(f"Email: {account_info['email']}\n")
                            f.write(f"User ID: {account_info['user_id']}\n")
                            f.write(f"Session ID: {account_info['session_id']}\n")
                            f.write(f"Created at: {account_info['creation_time']}\n")
                            f.write("="*50 + "\n")
                        print(Fore.GREEN + "[+] Account details saved to instagram_accounts.txt" + Style.RESET_ALL)
                    except Exception as e:
                        print(Fore.YELLOW + f"[-] Could not save account details: {e}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + "[-] Failed to create account" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"[-] Verification failed: {verify_result.get('message', 'Unknown error')}" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"[-] Failed to send verification email: {send_result.get('message', 'Unknown error')}" + Style.RESET_ALL)
    
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Process interrupted by user" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[!] An error occurred: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
