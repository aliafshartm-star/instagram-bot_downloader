
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
    save_metadata=False,
    post_metadata_txt_pattern=""
)


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
                "عضویت در کانال",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
            )
        ],
        [
            InlineKeyboardButton(
                "بررسی عضویت",
                callback_data="check_join"
            )
        ]
    ]

    text = (
        "❌ برای استفاده از ربات باید عضو کانال شوید."
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    joined = await check_join(
        context.bot,
        update.effective_user.id
    )

    if not joined:
        await force_join(update, context)
        return

    await update.message.reply_text(
        "✅ لینک اینستاگرام یا آیدی پیج را ارسال کنید."
    )


async def button_handler(update, context):
    query = update.callback_query

    await query.answer()

    joined = await check_join(
        context.bot,
        query.from_user.id
    )

    if joined:
        await query.message.reply_text(
            "✅ عضویت تایید شد. حالا لینک بفرست."
        )
    else:
        await force_join(update, context)


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

        if "instagram.com/p/" in text or "instagram.com/reel/" in text:

            shortcode = re.search(
                r"(?:p|reel)/([^/?]+)",
                text
            ).group(1)

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

            await asyncio.sleep(1)

            for file in os.listdir(folder):

                path = os.path.join(folder, file)

                if file.endswith(".jpg"):
                    await update.message.reply_photo(
                        photo=open(path, "rb")
                    )

                elif file.endswith(".mp4"):
                    await update.message.reply_video(
                        video=open(path, "rb")
                    )

        else:

            username = text.replace("@", "")

            profile = instaloader.Profile.from_username(
                loader.context,
                username
            )

            loader.download_profilepic(profile)

            for file in os.listdir():

                if file.startswith(username) and file.endswith(".jpg"):

                    await update.message.reply_photo(
                        photo=open(file, "rb")
                    )

                    break

    except Exception as e:

        await update.message.reply_text(
            f"❌ خطا:\n{str(e)}"
        )


def main():

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
