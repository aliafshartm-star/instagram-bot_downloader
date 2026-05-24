import os
import re
import asyncio
import instaloader

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

loader = instaloader.Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    save_metadata=False,
    post_metadata_txt_pattern="",
    quiet=True
)

loader.context.user_agent = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
)

# ---------------- FORCE JOIN ---------------- #

async def check_join(bot, user_id):

    try:

        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except:
        return False

async def force_join(update, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ بررسی عضویت",
                callback_data="check_join"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "❌ برای استفاده از ربات باید عضو کانال شوید."

    if update.callback_query:

        await update.callback_query.message.reply_text(
            text,
            reply_markup=reply_markup
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    joined = await check_join(
        context.bot,
        update.effective_user.id
    )

    if not joined:

        await force_join(update, context)
        return

    await update.message.reply_text(
        "🔥 لینک اینستاگرام یا آیدی پیج را ارسال کنید."
    )

# ---------------- BUTTON ---------------- #

async def button_handler(update, context):

    query = update.callback_query

    await query.answer()

    joined = await check_join(
        context.bot,
        query.from_user.id
    )

    if joined:

        await query.message.reply_text(
            "✅ عضویت تایید شد.\nحالا لینک یا آیدی بفرست."
        )

    else:

        await force_join(update, context)

# ---------------- DOWNLOAD ---------------- #

async def handle_message(update, context):

    joined = await check_join(
        context.bot,
        update.effective_user.id
    )

    if not joined:

        await force_join(update, context)
        return

    text = update.message.text.strip()

    try:

        # ---------- INSTAGRAM POST / REEL ---------- #

        if "instagram.com" in text:

            wait_msg = await update.message.reply_text(
                "⏳ در حال دانلود..."
            )

            match = re.search(
                r"/(p|reel|tv)/([^/?]+)",
                text
            )

            if not match:

                await wait_msg.edit_text(
                    "❌ لینک معتبر نیست."
                )

                return

            shortcode = match.group(2)

            post = instaloader.Post.from_shortcode(
                loader.context,
                shortcode
            )

            folder = os.path.join(
                DOWNLOAD_DIR,
                shortcode
            )

            loader.download_post(
                post,
                target=folder
            )

            await asyncio.sleep(2)

            sent = False

            for root, dirs, files in os.walk(folder):

                for file in files:

                    path = os.path.join(root, file)

                    try:

                        if file.endswith(".jpg"):

                            await update.message.reply_photo(
                                photo=open(path, "rb")
                            )

                            sent = True

                        elif file.endswith(".mp4"):

                            await update.message.reply_video(
                                video=open(path, "rb")
                            )

                            sent = True

                    except:
                        pass

            if sent:

                await wait_msg.delete()

            else:

                await wait_msg.edit_text(
                    "❌ فایل پیدا نشد."
                )

        # ---------- PROFILE PIC ---------- #

        else:

            wait_msg = await update.message.reply_text(
                "⏳ در حال دریافت عکس پروفایل..."
            )

            username = text.replace("@", "")

            profile = instaloader.Profile.from_username(
                loader.context,
                username
            )

            loader.download_profilepic(profile)

            found = False

            for file in os.listdir():

                if file.startswith(username) and file.endswith(".jpg"):

                    await update.message.reply_photo(
                        photo=open(file, "rb")
                    )

                    found = True
                    break

            if found:

                await wait_msg.delete()

            else:

                await wait_msg.edit_text(
                    "❌ عکس پروفایل پیدا نشد."
                )

    except Exception as e:

        await update.message.reply_text(
            f"❌ خطا:\n{str(e)}"
        )

# ---------------- MAIN ---------------- #

def main():

    asyncio.set_event_loop(
        asyncio.new_event_loop()
    )

    app = ApplicationBuilder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot Started...")

    app.run_polling()

if __name__ == "__main__":
    main()
