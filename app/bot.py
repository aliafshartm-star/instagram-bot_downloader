import os
import telebot
import yt_dlp
from instaloader import Instaloader, Profile

# --- تنظیمات اولیه ---
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHANNEL_ID = '@YourChannelID'  # 📢 آیدی کانال خودت رو اینجا بذار (مثلا @my_channel)

bot = telebot.TeleBot(BOT_TOKEN)
L = Instaloader()

# 🔐 تابع بررسی عضویت اجباری
def is_user_subbed(user_id):
    try:
        # وضعیت کاربر در کانال رو بررسی میکنه
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        # وضعیت‌های مجاز برای استفاده از ربات
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        # اگر خطایی داد (مثلا ربات ادمین کانال نباشه) برای اینکه ربات قفل نشه True برمیگردونه
        print(f"خطا در بررسی عضویت کانال: {e}")
        return True

# پیام خوش‌آمدگویی
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "سلام! به ربات دانلودر اینستاگرام خوش اومدی. 🚀\n\n"
        "📥 **دانلود پست و ریلز:** فقط کافیه لینک پست رو برام بفرستی.\n"
        "📸 **دانلود عکس پروفایل:** فقط کافیه آیدی (یوزرنیم) پیج رو بفرستی."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# مدیریت پیام‌های ورودی
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # 1. اول چک میکنیم کاربر عضو کانال هست یا نه
    if not is_user_subbed(user_id):
        # اگر عضو نبود، این پیام رو براش میفرستیم و دیگه بقیه کد اجرا نمیشه
        msg = f"⚠️ برای استفاده از این ربات، ابتدا باید عضو کانال ما شوید:\n\n📢 {CHANNEL_ID}\n\nبعد از عضویت، مجدداً لینک یا یوزرنیم خود را بفرستید."
        bot.reply_to(message, msg)
        return # خروج از تابع

    # 2. اگر عضو بود، بقیه مراحل دانلود اجرا میشه:
    text = message.text.strip()

    # تشخیص لینک اینستاگرام
    if "instagram.com" in text:
        bot.reply_to(message, "⏳ در حال دانلود پست/ریلز...")
        
        ydl_opts = {
            'outtmpl': f'downloads/{message.chat.id}_%(id)s.%(ext)s',
            'quiet': True,
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
            bot.reply_to(message, "❌ خطایی در دانلود پست رخ داد. مطمئن شو پیج عمومی (Public) باشه.")
            
    else:
        # بخش دانلود عکس پروفایل
        username = text.replace("@", "")
        bot.reply_to(message, f"⏳ در حال دریافت عکس پروفایل @{username}...")
        
        try:
            profile = Profile.from_username(L.context, username)
            profile_url = profile.profile_pic_url
            
            bot.send_photo(
                message.chat.id, 
                profile_url, 
                caption=f"📸 عکس پروفایل کیفیت اصلی @{username}\n\n👤 نام: {profile.full_name}\n👥 فالوورز: {profile.followers:,}"
            )
        except Exception as e:
            bot.reply_to(message, "❌ پیج پیدا نشد یا خطایی رخ داد. مطمئن شو یوزرنیم رو درست فرستادی.")

# تابع ارسال فایل و حذف از سرور
def send_file(chat_id, filepath):
    if not os.path.exists(filepath):
        return
    try:
        if filepath.endswith(('.mp4', '.mov', '.mkv')):
            with open(filepath, 'rb') as video:
                bot.send_video(chat_id, video)
        else:
            with open(filepath, 'rb') as photo:
                bot.send_photo(chat_id, photo)
    except Exception as e:
        print(f"Error sending file: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

print("ربات با سیستم عضویت اجباری روشن شد...")
bot.infinity_polling()
