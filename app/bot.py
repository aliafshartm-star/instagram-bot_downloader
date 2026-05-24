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

# ذخیره وضعیت موقت کاربران
user_states = {}
# برای اینکه یادت بمونه کاربر دکمه تایید رو زده یا نه
user_verified = {}

@app.route('/')
def home():
    return "ربات با موفقیت آپدیت شد! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 🔐 تابع بررسی سیستم عضویت اجباری در تلگرام
def is_user_subbed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"⚠️ Channel Check Error: {e}")
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
    clean_channel = CHANNEL_ID.replace("@", "")
    markup.add(InlineKeyboardButton("📢 عضویت در کانال ما", url=f"https://t.me/{clean_channel}"))
    markup.add(InlineKeyboardButton("✅ تایید عضویت و ورود", callback_data="check_sub"))
    return markup

# 🔙 دکمه بازگشت به منوی اصلی
def back_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data="go_to_main"))
    return markup

# 🏁 دستور /start (حالا در اولین بار قطعا قفل کانال را به همه نشان می‌دهد)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = None 
    user_verified[user_id] = False # در هر استارت، کاربر باید دوباره تایید بزند

    msg = f"⚠️ کاربر گرامی!\nبرای استفاده از خدمات ربات، ابتدا باید عضو کانال زیر شوید و سپس دکمه تایید را بزنید:"
    bot.send_message(message.chat.id, msg, reply_markup=sub_menu())

# 🎛️ مدیریت کلیک روی دکمه‌های شیشه‌ای
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # دکمه تایید عضویت
    if call.data == "check_sub":
        if is_user_subbed(user_id):
            user_verified[user_id] = True # کاربر تایید شد
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            bot.edit_message_text("سلام! به ربات دانلودر پیشرفته خوش آمدید. 🚀\nلطفاً یکی از گزینه‌های زیر را برای دانلود انتخاب کنید 👇", chat_id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ شما هنوز عضو کانال نشده‌اید یا ربات در کانال ادمین نیست!", show_alert=True)
        return

    # دکمه برگشت به منوی اصلی
    if call.data == "go_to_main":
        user_states[user_id] = None
        bot.edit_message_text("منوی اصلی ربات خدمت شما 👇\nلطفاً یک گزینه را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=main_menu())
        return

    # محافظت امنیتی: اگر دکمه‌های دیگر را زد ولی تایید نشده بود
    if not user_verified.get(user_id, False) or not is_user_subbed(user_id):
        bot.answer_callback_query(call.id, "⚠️ ابتدا باید عضویت خود را تایید کنید!")
        return

    # منوهای دانلود
    if call.data == "down_insta_profile":
        user_states[user_id] = "insta_profile"
        bot.edit_message_text("📸 **دانلود عکس پروفایل اینستاگرام**\n\n👤 لطفاً **آیدی (یوزرنیم)** پیج مورد نظر را بفرستید:\n(مثال: `cristiano`)", chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=back_menu())
        
    elif call.data == "down_insta_post":
        user_states[user_id] = "insta_post"
        bot.edit_message_text("🎬 **دانلود پست یا ریلز اینستاگرام**\n\n🔗 لطفاً لینک پست یا ریلز مورد نظر را بفرستید:", chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=back_menu())
        
    elif call.data == "down_youtube":
        user_states[user_id] = "youtube"
        bot.edit_message_text("🎥 **دانلود ویدیو از یوتیوب**\n\n🔗 لطفاً لینک ویدیو یا شورتس یوتیوب را بفرستید:", chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=back_menu())
        
    elif call.data == "bot_guide":
        guide_text = "💡 **راهنمای ربات:**\n\n1️⃣ ابتدا از منو نوع دانلود خود را انتخاب کنید.\n2️⃣ لینک یا آیدی مربوطه را بفرستید.\n3️⃣ فایل شما مستقیم در تلگرام ارسال می‌شود.\n\n🔄 در هر مرحله با زدن /start می‌توانید ربات را ریست کنید."
        bot.edit_message_text(guide_text, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=back_menu())

# 🧠 پردازش متن‌های ارسالی کاربر
@bot.message_handler(func=lambda message: True)
def handle_links(message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states.get(user_id)

    # بررسی اینکه آیا دکمه تایید را قبلا زده یا خیر
    if not user_verified.get(user_id, False) or not is_user_subbed(user_id):
        bot.reply_to(message, "⚠️ شما هنوز عضویت خود را تایید نکرده‌اید!", reply_markup=sub_menu())
        return

    if not state:
        bot.reply_to(message, "❌ لطفاً ابتدا از منوی اصلی مشخص کنید چه چیزی می‌خواهید دانلود کنید 👇", reply_markup=main_menu())
        return

    # پردازش دانلود بر اساس وضعیت کاربر
    if state == "insta_profile":
        username = text.replace("https://", "").replace("instagram.com/", "").split("/")[0].replace("@", "")
        bot.reply_to(message, f"⏳ در حال دریافت عکس پروفایل @{username}...")
        profile_link = f"https://instagram.com/{username}"
        download_and_send(message, profile_link, is_profile=True)

    elif state == "insta_post":
        if "instagram.com" in text:
            bot.reply_to(message, "⏳ در حال بررسی و دانلود پست/ریلز اینستاگرام...")
            download_and_send(message, text)
        else:
            bot.reply_to(message, "❌ لطفاً لینک معتبر اینستاگرام بفرستید.", reply_markup=back_menu())

    elif state == "youtube":
        if "youtube.com" in text or "youtu.be" in text:
            bot.reply_to(message, "⏳ در حال دانلود ویدیو یوتیوب...")
            download_and_send(message, text, is_youtube=True)
        else:
            bot.reply_to(message, "❌ لطفاً لینک معتبر یوتیوب بفرستید.", reply_markup=back_menu())

# 📥 تابع دانلود و ارسال
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
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=not is_profile)
            
            if is_profile:
                avatar_url = info.get('uploader_thumbnail') or info.get('thumbnails', [{}])[0].get('url')
                if avatar_url:
                    bot.send_photo(message.chat.id, avatar_url, caption="📸 عکس پروفایل پیج مورد نظر خدمت شما ✨\n\n🔄 برای دانلود مجدد از منو انتخاب کنید.", reply_markup=main_menu())
                    user_states[user_id] = None
                else:
                    bot.reply_to(message, "❌ عکس پروفایل پیدا نشد. مطمئن شو پیج عمومی باشه.", reply_markup=back_menu())
                return

            if 'entries' in info:
                for entry in info['entries']:
                    filename = ydl.prepare_filename(entry)
                    send_file(message.chat.id, filename)
            else:
                filename = ydl.prepare_filename(info)
                send_file(message.chat.id, filename)
                
            bot.send_message(message.chat.id, "✅ دانلود با موفقیت انجام شد!", reply_markup=main_menu())
            user_states[user_id] = None 
            
    except Exception as e:
        print(f"Global Download Error: {e}")
        bot.reply_to(message, "❌ خطایی در دانلود رخ داد! مطمئن شوید لینک/آیدی درست و پیج عمومی است.", reply_markup=back_menu())

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
    
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطا: {e}")
