import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from threading import Thread
from flask import Flask

# ================= ⚙️ دریافت تنظیمات از ENV رندر =================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
# ===============================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# ذخیره وضعیت موقت کاربران (برای اینکه بدانیم کاربر الان باید چه لینکی بفرستد)
user_states = {}

@app.route('/')
def home():
    return "ربات چندمنظوره دانلود با موفقیت روشن شد! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 🔐 تابع بررسی سیستم عضویت اجباری
def is_user_subbed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"⚠️ Channel Check Error: {e}")
        # اگر خطایی رخ داد (مثلا ربات هنوز ادمین نشده)، برای اینکه ربات قفل نکند True برمی‌گردانیم
        return True

# 📜 ساخت منوی اصلی دکمه‌ها
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 عکس پروفایل اینستا", callback_data="down_insta_profile"),
        InlineKeyboardButton("🎬 پست/ریلز اینستا", callback_data="down_insta_post")
    )
    markup.row(
        InlineKeyboardButton("🎥 ویدیو یوتیوب", callback_data="down_youtube")
    )
    markup.row(
        InlineKeyboardButton("📊 راهنمای ربات", callback_data="bot_guide")
    )
    return markup

# 📢 ساخت دکمه عضویت اجباری
def sub_menu():
    markup = InlineKeyboardMarkup()
    # دریافت لینک کانال (بدون @ برای ساخت لینک مستقیم)
    clean_channel = CHANNEL_ID.replace("@", "")
    markup.add(InlineKeyboardButton("📢 عضویت در کانال ما", url=f"https://t.me/{clean_channel}"))
    markup.add(InlineKeyboardButton("✅ تایید عضویت و ورود", callback_data="check_sub"))
    return markup

# 🏁 دستور /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = None # ریست کردن وضعیت کاربر

    if not is_user_subbed(user_id):
        msg = f"⚠️ کاربر گرامی!\nبرای استفاده از خدمات ربات، ابتدا باید عضو کانال زیر شوید و سپس دکمه تایید را بزنید:"
        bot.send_message(message.chat.id, msg, reply_markup=sub_menu())
    else:
        welcome_text = "سلام! به ربات دانلودر پیشرفته خوش آمدید. 🚀\n\nلطفاً یکی از گزینه‌های زیر را برای دانلود انتخاب کنید 👇"
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# 🎛️ مدیریت کلیک روی دکمه‌های شیشه‌ای (Callback Queries)
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # بررسی دکمه تایید عضویت
    if call.data == "check_sub":
        if is_user_subbed(user_id):
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            bot.edit_message_text("تشکر از عضویت شما! 🙏\nحالا گزینه مورد نظر خود را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ شما هنوز عضو کانال نشده‌اید!", show_alert=True)
        return

    # برای بقیه دکمه‌ها اول چک میکنیم هنوز عضو هست یا نه
    if not is_user_subbed(user_id):
        bot.answer_callback_query(call.id, "⚠️ شما عضو کانال نیستید!")
        bot.edit_message_text("⚠️ اشتراک شما قطع شده است. لطفاً ابتدا عضو کانال شوید:", chat_id, call.message.message_id, reply_markup=sub_menu())
        return

    # پردازش انتخاب منوها
    if call.data == "down_insta_profile":
        user_states[user_id] = "insta_profile"
        bot.edit_message_text("📸 **دانلود عکس پروفایل اینستاگرام**\n\n🔗 لطفاً لینک خودِ پیج را بفرستید:\n(مثال: `https://instagram.com/username`)", chat_id, call.message.message_id, parse_mode='Markdown')
        
    elif call.data == "down_insta_post":
        user_states[user_id] = "insta_post"
        bot.edit_message_text("🎬 **دانلود پست یا ریلز اینستاگرام**\n\n🔗 لطفاً لینک پست یا ریلز مورد نظر را بفرستید:", chat_id, call.message.message_id, parse_mode='Markdown')
        
    elif call.data == "down_youtube":
        user_states[user_id] = "youtube"
        bot.edit_message_text("🎥 **دانلود ویدیو از یوتیوب**\n\n🔗 لطفاً لینک ویدیو یا شورتس (Shorts) یوتیوب را بفرستید:", chat_id, call.message.message_id, parse_mode='Markdown')
        
    elif call.data == "bot_guide":
        guide_text = "💡 **راهنمای ربات:**\n\n1️⃣ ابتدا از منو نوع دانلود خود را انتخاب کنید.\n2️⃣ لینک مربوطه را بفرستید تا ربات پردازش کند.\n3️⃣ فایل شما مستقیم در تلگرام ارسال می‌شود.\n\n🔄 برای برگشت به منوی اصلی /start را بزنید."
        bot.edit_message_text(guide_text, chat_id, call.message.message_id, parse_mode='Markdown')

# 🧠 پردازش متن‌ها و لینک‌های ارسالی کاربر بر اساس دکمه‌ای که زده
@bot.message_handler(func=lambda message: True)
def handle_links(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states.get(user_id)

    # همیشه عضویت رو چک میکنیم
    if not is_user_subbed(user_id):
        bot.reply_to(message, "⚠️ شما عضو کانال نیستید!", reply_markup=sub_menu())
        return

    if not state:
        bot.reply_to(message, "❌ لطفاً ابتدا از منوی اصلی مشخص کنید چه چیزی می‌خواهید دانلود کنید 👇", reply_markup=main_menu())
        return

    # پردازش دانلود بر اساس وضعیت (State) کاربر
    if state == "insta_profile":
        if "instagram.com" in text:
            bot.reply_to(message, "⏳ در حال استخراج عکس پروفایل...")
            download_and_send(message, text, is_profile=True)
        else:
            bot.reply_to(message, "❌ لینک اشتباه است. لطفاً لینک پیج اینستاگرام را بفرستید.")

    elif state == "insta_post":
        if "instagram.com" in text and ('/p/' in text or '/reel/' in text or '/tv/' in text):
            bot.reply_to(message, "⏳ در حال بررسی و دانلود پست/ریلز اینستاگرام...")
            download_and_send(message, text)
        else:
            bot.reply_to(message, "❌ لینک اشتباه است. لطفاً لینک یک پست یا ریلز معتبر را بفرستید.")

    elif state == "youtube":
        if "youtube.com" in text or "youtu.be" in text:
            bot.reply_to(message, "⏳ در حال بررسی و دانلود ویدیو یوتیوب... (ممکن است کمی طول بکشد)")
            download_and_send(message, text, is_youtube=True)
        else:
            bot.reply_to(message, "❌ لینک اشتباه است. لطفاً لینک ویدیو یوتیوب را بفرستید.")

# 📥 تابع عمومی دانلود با yt-dlp و ارسال به تلگرام
def download_and_send(message, link, is_profile=False, is_youtube=False):
    user_id = message.from_user.id
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    ydl_opts = {
        'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    if is_youtube:
        ydl_opts['format'] = 'best' # برای یوتیوب بهترین کیفیت سرهم شده رو میگیره

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=not is_profile)
            
            # حالت دانلود عکس پروفایل
            if is_profile:
                avatar_url = info.get('uploader_thumbnail') or info.get('thumbnails', [{}])[0].get('url')
                if avatar_url:
                    bot.send_photo(message.chat.id, avatar_url, caption="📸 عکس پروفایل خدمت شما ✨")
                    user_states[user_id] = None # ریست وضعیت
                else:
                    bot.reply_to(message, "❌ عکس پروفایل پیدا نشد.")
                return

            # حالت دانلود ویدیو یا پست معمولی
            if 'entries' in info:
                for entry in info['entries']:
                    filename = ydl.prepare_filename(entry)
                    send_file(message.chat.id, filename)
            else:
                filename = ydl.prepare_filename(info)
                send_file(message.chat.id, filename)
                
            user_states[user_id] = None # ریست وضعیت بعد از اتمام موفقیت آمیز
            
    except Exception as e:
        print(f"Global Download Error: {e}")
        bot.reply_to(message, "❌ خطایی در دانلود فایل رخ داد! مطمئن شوید لینک درست و عمومی است.")

def send_file(chat_id, filepath):
    if not os.path.exists(filepath):
        return
    try:
        if filepath.lower().endswith(('.mp4', '.mov', '.mkv', '.avi')):
            with open(filepath, 'rb') as video:
                bot.send_video(chat_id, video)
        else:
            with open(filepath, 'rb') as photo:
                bot.send_photo(chat_id, photo)
    except Exception as e:
        print(f"Error Sending: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🔍 در حال اتصال به تلگرام...")
    try:
        bot_info = bot.get_me()
        print(f"✅ ربات همه کاره @{bot_info.username} با موفقیت دکمه‌ای و روشن شد.")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطا: {e}")
