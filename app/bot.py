import os
import telebot
import yt_dlp
from instaloader import Instaloader, Profile
from threading import Thread
from flask import Flask

# ================= ⚙️ دریافت تنظیمات از ENV رندر =================
# پایتون به صورت خودکار اطلاعات را از منوی Environment رندر می‌خواند
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
# ===============================================================

bot = telebot.TeleBot(BOT_TOKEN)
L = Instaloader()
app = Flask('')

@app.route('/')
def home():
    return "ربات اینستاگرام با موفقیت روشن شد و در حال کار است! 🚀"

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
        print(f"⚠️ Channel Check Error (Check if bot is admin): {e}")
        return True

# 📜 دستورات آغازین ربات
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "سلام! به ربات دانلودر اینستاگرام خوش اومدی. 🚀\n\n"
        "📥 **دانلود پست و ریلز:** فقط کافیه لینک پست رو برام بفرستی.\n"
        "📸 **دانلود عکس پروفایل:** فقط کافیه آیدی (یوزرنیم) پیج رو بفرستی.\n\n"
        "⚠️ توجه: برای استفاده از خدمات، باید حتماً عضو کانال ما باشید."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 🧠 بخش اصلی مدیریت و پردازش پیام‌ها
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_user_subbed(user_id):
        msg = f"⚠️ برای استفاده از خدمات ربات، ابتدا باید عضو کانال زیر شوید:\n\n📢 {CHANNEL_ID}\n\nبعد از عضویت، مجدداً لینک یا یوزرنیم خود را ارسال کنید."
        bot.reply_to(message, msg)
        return

    if "instagram.com" in text:
        bot.reply_to(message, "⏳ در حال بررسی و دانلود پست/ریلز از اینستاگرام...")
        
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
            
        ydl_opts = {
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                if 'entries' in info:
                    for entry in info['entries']:
                        filename = ydl.prepare_filename(entry)
                        send_file(message.chat.id, filename)
                else:
                    filename = ydl.prepare_filename(info)
                    send_file(message.chat.id, filename)
        except Exception as e:
            print(f"Download Error: {e}")
            bot.reply_to(message, "❌ خطایی در دانلود رخ داد! مطمئن شو لینک درست و پیج عمومی باشه.")
            
    else:
        username = text.replace("@", "").split("/")[0]
        bot.reply_to(message, f"⏳ در حال دریافت عکس پروفایل @{username}...")
        try:
            profile = Profile.from_username(L.context, username)
            caption_text = f"📸 عکس پروفایل @{username}\n\n👤 نام: {profile.full_name}\n👥 فالوورها: {profile.followers:,}"
            bot.send_photo(message.chat.id, profile.profile_pic_url, caption=caption_text)
        except Exception as e:
            print(f"Profile Error: {e}")
            bot.reply_to(message, "❌ پیج پیدا نشد یا خطایی رخ داد. نام کاربری را بدون علامت اضافی بفرستید.")

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
    
    print("🔍 در حال بررسی و اتصال به تلگرام...")
    try:
        bot_info = bot.get_me()
        print(f"✅ اتصال موفقیت‌آمیز بود! ربات @{bot_info.username} بدون خطا روشن شد.")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطا در روشن شدن ربات: {e}")
