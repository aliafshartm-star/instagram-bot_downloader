import os
import telebot
import yt_dlp
from instaloader import Instaloader, Profile

# ================= تنظیمات اصلی =================
# توکن ربات تلگرام را اینجا وارد کنید
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# آیدی کانال برای عضویت اجباری (حتماً ربات را در این کانال ادمین کنید)
# نمونه برای کانال عمومی: '@my_channel'
# نمونه برای کانال خصوصی: 100123456789- (آیدی عددی)
CHANNEL_ID = '@YourChannelID'  
# ===============================================

bot = telebot.TeleBot(BOT_TOKEN)
L = Instaloader()

# 🔐 تابع بررسی عضویت اجباری کاربر در کانال
def is_user_subbed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        # اگر ربات هنوز ادمین کانال نشده باشد، برای جلوگیری از قفل شدن کل ربات، موقتا True برمی‌گرداند
        print(f"⚠️ خطا در بررسی عضویت (احتمالاً ربات در کانال ادمین نیست): {e}")
        return True

# دستور /start و /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "سلام! به ربات دانلودر اینستاگرام خوش اومدی. 🚀\n\n"
        "📥 **دانلود پست و ریلز:** فقط کافیه لینک پست رو برام بفرستی.\n"
        "📸 **دانلود عکس پروفایل:** فقط کافیه آیدی (یوزرنیم) پیج رو بفرستی.\n\n"
        "⚠️ توجه: برای استفاده از ربات باید حتماً عضو کانال ما باشید."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# مدیریت و پردازش تمام پیام‌های ورودی
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # ۱. بررسی عضویت اجباری
    if not is_user_subbed(user_id):
        # راهنمایی برای آیدی کانال در متن پیام
        channel_link = f"https://t.me/{CHANNEL_ID.replace('@', '')}" if str(CHANNEL_ID).startswith('@') else "کانال ما"
        msg = f"⚠️ برای استفاده از خدمات ربات، ابتدا باید عضو کانال زیر شوید:\n\n📢 {CHANNEL_ID}\n\nبعد از عضویت، مجدداً لینک یا یوزرنیم خود را ارسال کنید."
        bot.reply_to(message, msg)
        return

    # ۲. اگر کاربر عضو بود -> پردازش درخواست اینستاگرام
    if "instagram.com" in text:
        # --- بخش دانلود پست و ریلز ---
        bot.reply_to(message, "⏳ در حال دانلود پست/ریلز از اینستاگرام...")
        
        # ساخت پوشه دانلود در صورت عدم وجود
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
                
                # اگر پست آلبومی (چندتایی) باشد
                if 'entries' in info:
                    for entry in info['entries']:
                        filename = ydl.prepare_filename(entry)
                        send_file(message.chat.id, filename)
                else:
                    # اگر تک پست یا ریلز باشد
                    filename = ydl.prepare_filename(info)
                    send_file(message.chat.id, filename)
                    
        except Exception as e:
            print(f"Insta Download Error: {e}")
            bot.reply_to(message, "❌ خطایی در دانلود پست رخ داد! مطمئن شو پیج عمومی (Public) باشه و لینک درسته.")
            
    else:
        # --- بخش دانلود عکس پروفایل ---
        username = text.replace("@", "").split("/")[0] # تمیز کردن یوزرنیم ورودی
        bot.reply_to(message, f"⏳ در حال دریافت عکس پروفایل @{username}...")
        
        try:
            profile = Profile.from_username(L.context, username)
            profile_url = profile.profile_pic_url
            
            caption_text = (
                f"📸 عکس پروفایل کیفیت اصلی @{username}\n\n"
                f"👤 نام: {profile.full_name}\n"
                f"👥 فالوورها: {profile.followers:,}\n"
                f" Following: {profile.followees:,}"
            )
            bot.send_photo(message.chat.id, profile_url, caption=caption_text)
        except Exception as e:
            print(f"Profile Download Error: {e}")
            bot.reply_to(message, "❌ پیج پیدا نشد یا خطایی رخ داد. مطمئن شو آیدی رو درست فرستادی.")

# تابع کمکی برای ارسال به تلگرام و حذف فایل از هارد سرور
def send_file(chat_id, filepath):
    if not os.path.exists(filepath):
        return
    try:
        # تشخیص نوع فایل برای ارسال درست
        if filepath.lower().endswith(('.mp4', '.mov', '.mkv', '.avi')):
            with open(filepath, 'rb') as video:
                bot.send_video(chat_id, video)
        else:
            with open(filepath, 'rb') as photo:
                bot.send_photo(chat_id, photo)
    except Exception as e:
        print(f"Telegram Sending Error: {e}")
    finally:
        # حذف فایل جهت جلوگیری از پر شدن حافظه هاست
        if os.path.exists(filepath):
            os.remove(filepath)

# اجرای امن ربات و تست اتصال اولیه
if __name__ == '__main__':
    try:
        print("🔍 در حال بررسی اتصال به تلگرام...")
        bot_info = bot.get_me()
        print(f"✅ اتصال برقرار شد! ربات @{bot_info.username} با موفقیت روشن شد و آماده به کاره.")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطای حیاتی: ربات نتوانست به تلگرام وصل شود.\nعلت خطا: {e}")
