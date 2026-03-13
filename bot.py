import os
import re
import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8615158623:AAGsJOvewkguA2OPM5czm0-zZPB-P4jooXA"

QR_IMAGE = "https://i.ibb.co/hxnx1G2X/Screenshot-2026-03-14-00-06-03-781-com-naviapp.png"

UPI_ID = "niggaseller@nyes"
ADMIN = "@eagleutrsubmissionbot"

valid_keys = {"EAGLE123", "VIP999"}

active_users = set()
awaiting_key = set()
awaiting_utr = set()

prediction_history = []

# ---------------- PERIOD ----------------

def get_period():
    now = datetime.datetime.utcnow()
    total_minutes = now.hour * 60 + now.minute
    return now.strftime("%Y%m%d") + str(10000 + total_minutes)

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("ENTER KEY", callback_data="enter_key")],
        [InlineKeyboardButton("BUY KEY ₹249", callback_data="buy_key")]
    ]

    text = "*🦅 EAGLE PREDICTION VIP*\n\n*SELECT OPTION*"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ---------------- BUTTON HANDLER ----------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

# -------- ENTER KEY --------

    if data == "enter_key":

        awaiting_key.add(query.from_user.id)

        await query.message.reply_text(
            "*PLEASE ENTER YOUR KEY*",
            parse_mode="Markdown"
        )

# -------- BUY KEY --------

    if data == "buy_key":

        keyboard = [
            [InlineKeyboardButton("SCAN QR", callback_data="scan_qr")],
            [InlineKeyboardButton("UPI PAY", callback_data="upi_pay")],
            [InlineKeyboardButton("SUBMIT UTR", callback_data="submit_utr")]
        ]

        await query.message.reply_text(
            "*BUY VIP KEY ₹249*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# -------- QR --------

    if data == "scan_qr":

        await context.bot.send_photo(
            chat_id=query.from_user.id,
            photo=QR_IMAGE,
            caption="*SCAN QR AND PAY ₹249*",
            parse_mode="Markdown"
        )

# -------- UPI --------

    if data == "upi_pay":

        text = f"*PAY ₹249*\n\n*UPI ID*\n{UPI_ID}"

        await query.message.reply_text(text, parse_mode="Markdown")

# -------- UTR --------

    if data == "submit_utr":

        awaiting_utr.add(query.from_user.id)

        await query.message.reply_text(
            "*PLEASE SUBMIT YOUR UTR*",
            parse_mode="Markdown"
        )

# -------- PREDICT --------

    if data == "predict":

        if query.from_user.id not in active_users:

            await query.message.reply_text(
                "*ENTER KEY FIRST*",
                parse_mode="Markdown"
            )
            return

        result = random.choice(["BIG", "SMALL"])

        if result == "SMALL":
            numbers = random.sample(range(0,5),2)
        else:
            numbers = random.sample(range(5,10),2)

        period = get_period()

        msg = f"""
*🦅 EAGLE PREDICTION*

*PERIOD*
{period}

*RESULT*
{result}

*NUMBERS*
{numbers[0]}  {numbers[1]}
"""

        prediction_history.append(f"{period} {result}")

        if len(prediction_history) > 10:
            prediction_history.pop(0)

        keyboard = [
            [
                InlineKeyboardButton("WIN", callback_data="win"),
                InlineKeyboardButton("LOSS", callback_data="loss")
            ],
            [
                InlineKeyboardButton("NEXT", callback_data="predict")
            ],
            [
                InlineKeyboardButton("📊", callback_data="history")
            ]
        ]

        await query.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# -------- HISTORY --------

    if data == "history":

        if not prediction_history:
            text = "*NO HISTORY*"
        else:
            text = "*LAST 10 PREDICTIONS*\n\n" + "\n".join(prediction_history)

        await query.message.reply_text(text, parse_mode="Markdown")

# ---------------- TEXT HANDLER ----------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    text = update.message.text.strip()

# -------- KEY INPUT --------

    if user in awaiting_key:

        awaiting_key.remove(user)

        if text in valid_keys:

            active_users.add(user)

            keyboard = [
                [InlineKeyboardButton("START PREDICT", callback_data="predict")]
            ]

            await update.message.reply_text(
                "*KEY ACTIVATED*\n\n*PLEASE PLAY WITH LEVEL 2 🚀*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        else:

            await update.message.reply_text(
                "*INVALID KEY*",
                parse_mode="Markdown"
            )

        return

# -------- UTR INPUT --------

    if user in awaiting_utr:

        awaiting_utr.remove(user)

        if re.match(r"^\d{11,13}$", text):

            await update.message.reply_text(
                "*THANK YOU SO MUCH FOR YOUR TRUST*\n\n"
                f"*PLEASE SHARE YOUR UTR WITH*\n{ADMIN}\n\n"
                "*FOR FAST QUERY*",
                parse_mode="Markdown"
            )

        else:

            await update.message.reply_text(
                "*INVALID UTR*\n*SEND 11-13 DIGITS*",
                parse_mode="Markdown"
            )

# ---------------- MAIN ----------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

app.run_polling()
