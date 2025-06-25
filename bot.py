import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

load_dotenv()

# === SETTINGS ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Hi! I am Pankaj Pal, your Background Remover Bot.\n\n"
        "👉 Just send me any photo, and I’ll remove its background in seconds!\n"
        "🗣️ You can say 'hi', 'help', or simply send a photo now!"
    )
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me any photo and I will send it back without background. Just try sending a picture!"
    )

async def say_hi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in ["hi", "hello", "hii", "hey"]:
        await update.message.reply_text(
            "I am Pankaj Pal! Please send a photo and I will remove its background. 😊"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"{user.id}_input.png"
    await file.download_to_drive(file_path)
    await update.message.reply_text("⏳ Removing background from your photo. Please wait...")

    with open(file_path, 'rb') as img:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )

    if response.status_code == 200:
        out_path = f"{user.id}_no_bg.png"
        with open(out_path, "wb") as out:
            out.write(response.content)

        await update.message.reply_text("✅ Done! Here is your photo without background:")
        await update.message.reply_photo(photo=open(out_path, 'rb'))

        admin_msg = (
            f"User @{user.username or user.first_name} (ID: {user.id}) "
            "used the bot. Here is the background-removed photo:"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=open(out_path, 'rb'))

        os.remove(out_path)
    else:
        await update.message.reply_text(
            "❌ Sorry, I could not remove the background. Please try again later."
        )

    if os.path.exists(file_path):
        os.remove(file_path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT, say_hi))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running... ✅")
    app.run_polling()