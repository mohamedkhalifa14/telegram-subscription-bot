import telebot
from telebot import types
import datetime
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATA_FILE = "subscribers.json"

bot = telebot.TeleBot(BOT_TOKEN)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def is_subscribed(user_id):
    data = load_data()
    if str(user_id) in data:
        expiry = datetime.datetime.fromisoformat(data[str(user_id)])
        if expiry > datetime.datetime.now():
            return True
    return False

@bot.message_handler(commands=['start'])
def start(msg):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💳 تجديد / اشتراك جديد", callback_data="subscribe")
    markup.add(btn1)
    bot.send_message(msg.chat.id, "👋 أهلاً بك في نظام الاشتراكات المدفوعة!

اضغط الزر أدناه لبدء الاشتراك أو التجديد.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "subscribe")
def subscribe(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
                     "💰 تكلفة الاشتراك: 100 جنيه / شهر\n\nقم بالدفع وأرسل لي إثبات الدفع (صورة أو لقطة شاشة).")

@bot.message_handler(content_types=['photo'])
def payment_proof(msg):
    user_id = msg.from_user.id
    bot.reply_to(msg, "✅ تم استلام إثبات الدفع.\n\nكم مدة الاشتراك التي تم دفعها؟ (بالأيام مثلاً 30)")
    bot.register_next_step_handler(msg, lambda m: add_subscription(user_id, m))

def add_subscription(user_id, msg):
    try:
        days = int(msg.text.strip())
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        data = load_data()
        data[str(user_id)] = expiry.isoformat()
        save_data(data)
        bot.reply_to(msg, f"✅ تم تفعيل اشتراكك لمدة {days} يومًا (حتى {expiry.strftime('%Y-%m-%d')})")
        try:
            bot.unban_chat_member(GROUP_ID, user_id)
            bot.invite_link = bot.create_chat_invite_link(GROUP_ID, member_limit=1)
            bot.send_message(user_id, f"🎟️ رابط الانضمام للجروب:\n{bot.invite_link.invite_link}")
        except Exception as e:
            bot.send_message(user_id, "⚠️ لم أتمكن من إرسال الدعوة للجروب، تأكد أن البوت مشرف.")
    except:
        bot.reply_to(msg, "❌ يرجى إدخال رقم الأيام فقط.")

import threading
import time

def check_expired():
    while True:
        data = load_data()
        changed = False
        for uid, expiry_str in list(data.items()):
            expiry = datetime.datetime.fromisoformat(expiry_str)
            if expiry <= datetime.datetime.now():
                try:
                    bot.kick_chat_member(GROUP_ID, int(uid))
                    bot.send_message(int(uid), "❌ انتهى اشتراكك وتم إزالتك من الجروب.")
                except:
                    pass
                del data[uid]
                changed = True
        if changed:
            save_data(data)
        time.sleep(3600)

threading.Thread(target=check_expired, daemon=True).start()

print("✅ البوت شغال ...")
bot.infinity_polling()
