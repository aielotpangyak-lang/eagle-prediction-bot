import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8615158623:AAFywI6ygU2BTPnnKA4Zb8ZvZkbta-yy2Lk"
UPI_ID = "niggaseller@nyes"
ADMIN = "@EagleAdminofc"

valid_keys = {"EAGLE123", "VIP999"}
active_users = set()
user_level = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("Enter Key", callback_data="enter")],
        [InlineKeyboardButton("Buy Key ₹249", callback_data="buy")]
    ]

    await update.message.reply_text(
        "🦅 Eagle Prediction\n\nSelect option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "enter":
        await query.message.reply_text("Use command:\n/addkey YOUR_KEY")

    if query.data == "buy":

        msg = f"""
🦅 Eagle Prediction VIP

Price: ₹249

UPI ID:
{UPI_ID}

Payment karne ke baad UTR submit karo:

/utr YOUR_UTR

Admin:
{ADMIN}
"""
        await query.message.reply_text(msg)


async def utr(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Use:\n/utr YOUR_UTR")
        return

    utr_code = context.args[0]

    await update.message.reply_text(
        f"UTR Received: {utr_code}\n\nPlease contact admin:\n{ADMIN}"
    )


async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Use:\n/addkey KEY")
        return

    key = context.args[0]

    if key in valid_keys:

        active_users.add(update.effective_user.id)

        keyboard = [
            [InlineKeyboardButton("Play Level 1", callback_data="level1")],
            [InlineKeyboardButton("Play Level 2", callback_data="level2")],
            [InlineKeyboardButton("Play Level 3", callback_data="level3")]
        ]

        await update.message.reply_text(
            "✅ Key Activated\n\nSelect Play Level:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        await update.message.reply_text("❌ Invalid Key")


async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    lvl = int(query.data.replace("level", ""))

    user_level[query.from_user.id] = lvl

    await query.message.reply_text(
        f"🎮 Level {lvl} Selected\n\nUse /predict to start"
    )


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in active_users:
        await update.message.reply_text("Enter key first")
        return

    result = random.choice(["Big", "Small"])

    if result == "Small":
        numbers = random.sample(range(0,5),2)
    else:
        numbers = random.sample(range(5,10),2)

    msg = f"""
🦅 Eagle Prediction

Result: {result}

Numbers:
{numbers[0]}  {numbers[1]}

Use /next for next prediction
"""

    await update.message.reply_text(msg)


async def nextpred(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await predict(update, context)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("utr", utr))
app.add_handler(CommandHandler("addkey", addkey))
app.add_handler(CommandHandler("predict", predict))
app.add_handler(CommandHandler("next", nextpred))

app.add_handler(CallbackQueryHandler(level, pattern="^level"))
app.add_handler(CallbackQueryHandler(buttons))

import asyncio

async def main():
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
