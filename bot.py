import os
import re
import random
import datetime
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = "8615158623:AAGsJOvewkguA2OPM5czm0-zZPB-P4jooXA"

QR_IMAGE = "https://i.ibb.co/hxnx1G2X/Screenshot-2026-03-14-00-06-03-781-com-naviapp.png"
UPI_ID = "niggaseller@nyes"
ADMIN_BOT = "@eagleutrsubmissionbot"

VALID_KEYS = {"EAGLE123", "VIP999"}

# ================= MEMORY STATE =================

active_users = set()
awaiting_key = set()
awaiting_utr = set()

# per-user last prediction minute (lock)
last_prediction_minute = {}

# per-user stats
user_stats = defaultdict(lambda: {"win": 0, "loss": 0})

# global prediction history (last 10)
prediction_history = []

# ================= UTIL =================

def get_period():
    """Generate period synced to UTC minute."""
    now = datetime.datetime.utcnow()
    date = now.strftime("%Y%m%d")
    minutes = now.hour * 60 + now.minute
    return f"{date}1000{10000 + minutes}"

def current_minute_key():
    now = datetime.datetime.utcnow()
    return now.strftime("%Y%m%d%H%M")

def prediction():
    result = random.choice(["BIG", "SMALL"])
    if result == "SMALL":
        nums = random.sample(range(0, 5), 2)
    else:
        nums = random.sample(range(5, 10), 2)
    return result, nums

def stats_text(uid):
    w = user_stats[uid]["win"]
    l = user_stats[uid]["loss"]
    total = w + l
    wr = (w / total * 100) if total > 0 else 0
    return f"*📊 STATS*\n\n*WIN:* {w}\n*LOSS:* {l}\n*WR:* {wr:.0f}%"

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ENTER KEY", callback_data="enter_key")],
        [InlineKeyboardButton("BUY KEY ₹249", callback_data="buy_key")],
    ]
    text = "*🦅 EAGLE PREDICTION VIP*\n\n*SELECT OPTION*"
    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def utr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /utr 123456789012
    msg = update.message.text.strip()
    parts = msg.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("*USAGE:*\n`/utr 123456789012`", parse_mode="Markdown")
        return
    utr = parts[1].strip()
    if re.match(r"^\d{11,13}$", utr):
        await update.message.reply_text(
            "*THANK YOU SO MUCH FOR YOUR TRUST*\n\n"
            f"*PLEASE SHARE YOUR UTR WITH*\n{ADMIN_BOT}\n\n"
            "*FOR FAST QUERY*",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("*INVALID UTR*\n*SEND 11-13 DIGITS*", parse_mode="Markdown")

# ================= CALLBACK HANDLER =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id

    # -------- ENTER KEY --------
    if data == "enter_key":
        awaiting_key.add(uid)
        await query.message.edit_text("*PLEASE ENTER YOUR KEY*", parse_mode="Markdown")
        return

    # -------- BUY KEY --------
    if data == "buy_key":
        keyboard = [
            [InlineKeyboardButton("SCAN QR", callback_data="scan_qr")],
            [InlineKeyboardButton("UPI PAY", callback_data="upi_pay")],
            [InlineKeyboardButton("SUBMIT UTR", callback_data="submit_utr")],
        ]
        await query.message.edit_text(
            "*BUY VIP KEY ₹249*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # -------- QR --------
    if data == "scan_qr":
        await context.bot.send_photo(
            chat_id=uid,
            photo=QR_IMAGE,
            caption="*SCAN QR AND PAY ₹249*",
            parse_mode="Markdown",
        )
        return

    # -------- UPI --------
    if data == "upi_pay":
        text = f"*PAY ₹249*\n\n*UPI ID*\n{UPI_ID}"
        await query.message.reply_text(text, parse_mode="Markdown")
        return

    # -------- UTR --------
    if data == "submit_utr":
        awaiting_utr.add(uid)
        await query.message.reply_text(
            "*SEND YOUR UTR*\n\n`/utr 123456789012`",
            parse_mode="Markdown",
        )
        return

    # -------- PREDICT --------
    if data == "predict":
        if uid not in active_users:
            await query.answer("ENTER KEY FIRST", show_alert=True)
            return

        minute_key = current_minute_key()
        if last_prediction_minute.get(uid) == minute_key:
            await query.answer("WAIT NEXT PERIOD", show_alert=True)
            return

        last_prediction_minute[uid] = minute_key

        result, nums = prediction()
        period = get_period()

        msg = (
            "*🦅 EAGLE PREDICTION*\n\n"
            f"*PERIOD*\n{period}\n\n"
            f"*RESULT*\n{result}\n\n"
            f"*NUMBERS*\n{nums[0]}  {nums[1]}"
        )

        prediction_history.append(f"{period} {result}")
        if len(prediction_history) > 10:
            prediction_history.pop(0)

        keyboard = [
            [
                InlineKeyboardButton("WIN", callback_data="win"),
                InlineKeyboardButton("LOSS", callback_data="loss"),
            ],
            [InlineKeyboardButton("NEXT", callback_data="predict")],
            [InlineKeyboardButton("📊 HISTORY", callback_data="history")],
        ]

        # edit for smooth UI
        await query.message.edit_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # -------- WIN --------
    if data == "win":
        user_stats[uid]["win"] += 1
        await query.answer("WIN RECORDED")
        await query.message.reply_text(stats_text(uid), parse_mode="Markdown")
        return

    # -------- LOSS --------
    if data == "loss":
        user_stats[uid]["loss"] += 1
        await query.answer("LOSS RECORDED")
        await query.message.reply_text(stats_text(uid), parse_mode="Markdown")
        return

    # -------- HISTORY --------
    if data == "history":
        if not prediction_history:
            text = "*NO HISTORY*"
        else:
            text = "*LAST 10 PREDICTIONS*\n\n" + "\n".join(prediction_history)
        await query.message.reply_text(text, parse_mode="Markdown")
        return

# ================= TEXT HANDLER =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # ---- KEY INPUT ----
    if uid in awaiting_key:
        awaiting_key.remove(uid)
        if text in VALID_KEYS:
            active_users.add(uid)
            keyboard = [[InlineKeyboardButton("START PREDICT", callback_data="predict")]]
            await update.message.reply_text(
                "*KEY ACTIVATED*\n\n*PLEASE PLAY WITH LEVEL 2 🚀*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("*INVALID KEY*", parse_mode="Markdown")
        return

    # ---- UTR INPUT (fallback if user typed directly) ----
    if uid in awaiting_utr:
        awaiting_utr.remove(uid)
        if re.match(r"^\d{11,13}$", text):
            await update.message.reply_text(
                "*THANK YOU SO MUCH FOR YOUR TRUST*\n\n"
                f"*PLEASE SHARE YOUR UTR WITH*\n{ADMIN_BOT}\n\n"
                "*FOR FAST QUERY*",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "*INVALID UTR*\n*SEND 11-13 DIGITS*",
                parse_mode="Markdown",
            )

# ================= MAIN =================

def main():
    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN env variable or replace in code.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("utr", utr_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # smoother restarts
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
