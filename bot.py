import os
import json
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from utils import generate_period, generate_prediction
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",")]
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Simple file storage
DATA_FILE = "bot_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"valid_keys": [], "activated_users": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()
valid_keys = set(data["valid_keys"])
activated_users = set(data["activated_users"])
last_prediction = {}  # user_id -> minute_of_day

def is_admin(user_id):
    return user_id in ADMIN_IDS

def persist():
    data["valid_keys"] = list(valid_keys)
    data["activated_users"] = list(activated_users)
    save_data(data)

# -------------------- Handlers --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ENTER KEY", callback_data="enter_key")],
        [InlineKeyboardButton("BUY KEY ₹249", callback_data="buy_key")]
    ]
    await update.message.reply_text(
        "Eagle Prediction VIP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "enter_key":
        context.user_data["state"] = "awaiting_key"
        await query.edit_message_text("PLEASE ENTER YOUR KEY")

    elif data == "buy_key":
        # Send QR code (make sure you have qr.png in your repo)
        with open("qr.png", "rb") as f:
            await query.message.reply_photo(f, caption="Scan QR to pay ₹249")
        await query.message.reply_text(
            "UPI ID: eagle@paytm\n\n"
            "SEND YOUR UTR\n"
            "/utr 123456789012"
        )
        await query.edit_message_text("Payment instructions sent above.")

    elif data == "predict":
        await show_prediction(update, context, edit=False)

    elif data == "next":
        await show_prediction(update, context, edit=True)

async def handle_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") != "awaiting_key":
        return
    key = update.message.text.strip()
    if key in valid_keys:
        valid_keys.discard(key)
        activated_users.add(update.effective_user.id)
        persist()
        context.user_data["state"] = None
        await update.message.reply_text(
            "KEY ACTIVATED\nPLEASE PLAY WITH LEVEL 2 🚀"
        )
        keyboard = [[InlineKeyboardButton("PREDICT", callback_data="predict")]]
        await update.message.reply_text(
            "Click to start prediction",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("INVALID KEY")

async def utr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = " ".join(context.args)
    if not utr:
        await update.message.reply_text("Usage: /utr <UTR>")
        return
    user = update.effective_user
    for admin in ADMIN_IDS:
        await context.bot.send_message(
            admin,
            f"UTR from {user.id} (@{user.username}): {utr}"
        )
    await update.message.reply_text(
        "UTR received. Our team will verify and send your key.\n"
        "CONTACT @eagleutrsubmissionbot"
    )

async def show_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update.effective_user.id
    if user_id not in activated_users:
        msg = "Please activate key first."
        if edit:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    now = datetime.utcnow()
    current_minute = now.hour * 60 + now.minute
    last = last_prediction.get(user_id)

    if last == current_minute:
        msg = "WAIT NEXT PERIOD"
        if edit:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    period = generate_period(now)
    result, numbers = generate_prediction()
    last_prediction[user_id] = current_minute

    text = (
        f"EAGLE PREDICTION\n\n"
        f"PERIOD\n{period}\n\n"
        f"RESULT\n{result}\n\n"
        f"NUMBERS\n{numbers}"
    )
    keyboard = [[InlineKeyboardButton("NEXT", callback_data="next")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# -------------------- Admin Commands --------------------
async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addkey <key>")
        return
    key = args[0]
    valid_keys.add(key)
    persist()
    await update.message.reply_text(f"Key '{key}' added.")

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if valid_keys:
        await update.message.reply_text("Valid keys:\n" + "\n".join(valid_keys))
    else:
        await update.message.reply_text("No keys.")

async def delkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /delkey <key>")
        return
    key = args[0]
    if key in valid_keys:
        valid_keys.discard(key)
        persist()
        await update.message.reply_text(f"Key '{key}' removed.")
    else:
        await update.message.reply_text("Key not found.")

# -------------------- Webhook Setup --------------------
app = Flask(__name__)

def create_application():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_key_input))
    application.add_handler(CommandHandler("utr", utr_handler))
    application.add_handler(CommandHandler("addkey", addkey))
    application.add_handler(CommandHandler("listkeys", listkeys))
    application.add_handler(CommandHandler("delkey", delkey))
    return application

telegram_app = create_application()

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), telegram_app.loop)
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    # Set webhook on startup
    asyncio.run(telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook/{TOKEN}"))
    # Run Flask server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))