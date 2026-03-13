import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8615158623:AAGnj0EoEn-8GqYpPTva8ordTU0lWuMfZg8"
UPI_ID = "niggaseller@nyes"
ADMIN = "@EagleAdminofc"

valid_keys = {"EAGLE123","VIP999"}
active_users = set()

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
Price: ₹249

UPI ID:
{UPI_ID}

Payment ke baad UTR bhejo:
/utr YOUR_UTR

Admin:
{ADMIN}
"""
        await query.message.reply_text(msg)

async def utr(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Use /utr YOUR_UTR")
        return

    await update.message.reply_text(
        f"UTR received.\nContact admin:\n{ADMIN}"
    )

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Use /addkey KEY")
        return

    key = context.args[0]

    if key in valid_keys:
        active_users.add(update.effective_user.id)
        await update.message.reply_text("Key activated.\nUse /predict")
    else:
        await update.message.reply_text("Invalid key")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in active_users:
        await update.message.reply_text("Enter key first")
        return

    result = random.choice(["Big","Small"])

    if result == "Small":
        numbers = random.sample(range(0,5),2)
    else:
        numbers = random.sample(range(5,10),2)

    msg = f"""
Result: {result}

Numbers:
{numbers[0]}  {numbers[1]}

Use /next
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
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
