import random
import os
try:
  import requests
  import random
  import threading
  import time
  from ms4 import UserAgentGenerator
  from uuid import uuid4
  from secrets import token_hex
  from user_agent import generate_user_agent
  from rich.console import Console
  from rich.table import Table
  from rich.text import Text
except:
	os.system("pip install ms4==2.10.0 rich")
	
import requests
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor as tot
from ms4 import UserAgentGenerator
from user_agent import generate_user_agent
from uuid import uuid4
from secrets import token_hex
from rich.console import Console
from rich.table import Table
from rich.text import Text

All = "qwertyuiopasdfghjklzxcvbnm"
Num = "0123456789"

E = '\033[1;31m'
X = '\033[1;33m'
F = '\033[2;32m'
M = '\x1b[1;37m'
B = '\x1b[38;5;208m'
memo = random.randint(100, 300)
O = f'\x1b[38;5;{memo}m'

def nx():
    os.system("clear")
    Banner = f"""{B}{E}=============================={B}
|{F}[+] YouTube    : {B}| أحمد الحراني 
|{F}[+] TeleGram   : {B} maho_s9    
|{F}[+] Instagram  : {B} ahmedalharrani 
|{F}[+] Tool  : {B}Available Username IG |
|{F}[+] sever  : {B} Web |
{E}==============================
"""
    for mm in Banner.splitlines():
        time.sleep(0.05)
        print(mm)

nx()

token = input(f' {F}({M}1{F}) {M} Enter Token{F}  ' + O)
print(X + ' ═════════════════════════════════  ')
ID = input(f' {F}({M}2{F}) {M} Enter ID{F}  ' + O)

console = Console()
bb = 0
gg = 0

def Alhrrani(user, proxy):
    global gg, bb
    csr = token_hex(8) * 2
    headers = {
    'authority': 'www.instagram.com',
    'accept': '*/*',
    'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.instagram.com',
    'referer': 'https://www.instagram.com/accounts/login/?next=%2F&source=logged_out_homepage',
    'sec-ch-prefers-color-scheme': 'light',
    'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
    'sec-ch-ua-full-version-list': '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6327.4"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-model': '"23127PN0CC"',
    'sec-ch-ua-platform': '"Android"',
    'sec-ch-ua-platform-version': '"11.0.0"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': generate_user_agent(),
    'x-asbd-id': '129477',
    'x-csrftoken': csr,
    'x-ig-app-id': '1217981644879628',
    'x-ig-www-claim': '0',
    'x-instagram-ajax': '1016159378',
    'x-requested-with': 'XMLHttpRequest',
}

    data = {
    'enc_password': '#PWD_INSTAGRAM_BROWSER:10:1725333010:AdVQAIKFZ2bJpOIbQENgiygmpue333TXS56Z8NG253JS1LgjbV26LsUm/NuoCsYoNvEgHCTkGBmpCsx7KmPiTnur/Bqzb/hsjbj550lj1SiJEL8RkKyydce7O7cAYiTkAsaitYno1s045I/A5BU9KA==',
    'loginAttemptSubmissionCount': '0',
    'optIntoOneTap': 'false',
    'queryParams': '{"next":"/","source":"logged_out_homepage"}',
    'trustedDeviceRecords': '{}',
    'username': user,
}
    try:
      req = requests.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/', headers=headers, data=data, proxies={'http': proxy}).text
      if "showAccountRecoveryModal" in req:
          bb += 1
      else:
          gg += 1
          tlg = f'''
 Hi hunt Username INSTAGRAM
⋘─────━*AHMED*━─────⋙
Good Username : {user}
Instagram ==√
BY : @maho_s9 √ CH : @maho9s
⋘─────━*AHMED*━─────⋙'''
          print(F + tlg)
          requests.post(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text={tlg}')
    except:
        bb += 1
        pass
 

    
def mahos(user, proxy):
    global gg, bb
    try:        
        csr = token_hex(8) * 2
        uid = uuid4().hex.upper()
        miid = token_hex(13).upper()
        dtr = token_hex(13)

        cookies = {
            'csrftoken': csr,
            'dpr': '2.1988937854766846',
            'ps_n': '0',
            'ps_l': '0',
            'mid': miid,
            'ig_did': uid,
            'datr': dtr,
            'ig_nrcb': '1',
        }

        headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'ar-YE,ar;q=0.9,en-YE;q=0.8,en-US;q=0.7,en;q=0.6',
            'content-type': 'application/x-www-form-urlencoded',
            'dpr': '2.19889',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/emailsignup/',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Linux"',
            'sec-ch-ua-platform-version': '""',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': str(UserAgentGenerator()),
            'viewport-width': '891',
            'x-asbd-id': '129477',
            'x-csrftoken': csr,
            'x-ig-app-id': '936619743392459',
            'x-ig-www-claim': '0',
            'x-instagram-ajax': '1012280089',
            'x-requested-with': 'XMLHttpRequest',
        }

        timestamp = str(time.time()).split('.')[0]
        data = {
           'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{timestamp}:mahos999',
            'email': 'mahos@mahos.com',
            'first_name': 'Ahmedalhrrani',
            'username': user,
            'client_id': miid,
            'seamless_login_enabled': '1',
            'opt_into_one_tap': 'false',
        }

        res = requests.post(
            'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/',
            cookies=cookies,
            headers=headers,
            data=data,
            proxies={'http': proxy}
        ).text

        if '"dryrun_passed":true,' in res:
            gg += 1
            tlg = f'''
 Hi hunt Username INSTAGRAM
⋘─────━*AHMED*━─────⋙
Good Username : {user}
Instagram ==√
BY : @maho_s9 √ CH : @maho9s
⋘─────━*AHMED*━─────⋙'''
            print(F + tlg)
            requests.post(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text={tlg}')
        elif '"errors"' in res and '"username_is_taken"' in res and '"dryrun_passed": false,' in res or 'username_has_special_char' in res:      
            bb += 1
        else:
            bb += 1
            Alhrrani(user, proxy)
    except:
        bb += 1    	
        Alhrrani(user, proxy)
        pass
    	
        

def Ahmed(user, proxy):
    global gg, bb
    headers = {
    'authority': 'www.instagram.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'dpr': '2.75',
    'referer': f'https://www.instagram.com/{user}/',
    'sec-ch-prefers-color-scheme': 'light',
    'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
    'sec-ch-ua-full-version-list': '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6327.4"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-model': '"23127PN0CC"',
    'sec-ch-ua-platform': '"Android"',
    'sec-ch-ua-platform-version': '"11.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': generate_user_agent(),
    'viewport-width': '980',
}

    try:
      res = requests.get(f'https://www.instagram.com/{user}/', headers=headers, proxies={'http': proxy}).text
      if "<title>Instagram</title>" in res:         
          mahos(user, proxy)
      elif "الملف الشخصي" in res and user in res or user in res:
          bb += 1
      else:
          bb += 1
          mahos(user, proxy)
    except:
        bb += 1
        pass
        
    os.system('clear')
    table = Table(title="Instagram username")
    table.add_column("Type", justify="center", style="cyan", no_wrap=True)
    table.add_column("Count", justify="center", style="magenta")
    table.add_row("GoodInstaUser", str(gg), style="green")
    table.add_row("BadInstaUser", str(bb), style="red")   
    table.add_row("Username", user, style="white")
    table.add_row("Dev", "AHMED ~~ @maho_s9")

    console.print(table)

def Gen(G):
    usery = ''
    i = 0 
    while i < len(G):
        if G[i] == '#':
            usery += random.choice(All + Num)  
        elif G[i] == '*':
            usery += random.choice(All)  
        elif G[i] == '"':
            usery += random.choice(Num)
        elif G[i] == '_':
            usery += '_'  
        elif G[i] == '.':
            usery += '.'  
        elif G[i:i+2] == '@@':
            usery += random.choice(All) * 2 
            i += 1
        elif G[i:i+2] == '§§':
            usery += random.choice(Num) * 2  
            i += 1  
        else:
            usery += G[i]
        
        i += 1  
    
    return usery

Gs = [
    "#_#_#",
    "_#_#_",
    "##.##",
    "#.###",
    "##_##",
    "###__",
    "__###",
    "**.**",
    "@@_§§",
    "§§.@@",
    "§§_@@",
    "@@.§§",
    "_###_",
    '**_""',
    ".####",
    "#.#.#",
    "#_#.#",
    "#.#_#",
    "#.#_#",
    "##_##",
    "#_###",
    "###_#",
    "#.##_",
    "##.##",
    "#.##.#",
    "#_##.#"
]
with tot(max_workers=2) as los:
  while True:
    ah = random.choice(Gs)
    user = Gen(ah)
    ip = ".".join(str(random.randint(0, 255)) for _ in range(4))        
    pl = [19, 20, 21, 22, 23, 24, 25, 80, 53, 111, 110, 443, 8080, 139, 445, 512, 513, 514, 4444, 2049, 1524, 3306, 5900]
    port = random.choice(pl)
    proxy = ip + ":" + str(port)        
    los.submit(Ahmed, user, proxy)
    
    
