from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# ===== CONFIG =====
BOT_TOKEN = "SEU_BOT_TOKEN_AQUI"  # 🔴 coloque seu token
BASE_URL = "https://SEU-APP.up.railway.app"  # 🔴 coloque a URL do Railway

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 Daily - $2.99", callback_data="daily")],
        [InlineKeyboardButton("💎 Monthly - $12.99", callback_data="monthly")],
        [InlineKeyboardButton("💎 Lifetime - $39.99", callback_data="lifetime")]
    ]

    await update.message.reply_text(
        "🔥 VIP ACCESS 🔥\n\nChoose your plan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== BOTÕES =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    plan = query.data

    try:
        response = requests.get(f"{BASE_URL}/create-checkout/{plan}/{user_id}")
        data = response.json()

        payment_url = data.get("url")

        await query.message.reply_text(
            "💳 Complete your payment:\n\n" + payment_url
        )

    except Exception:
        await query.message.reply_text("❌ Error generating payment link.")

# ===== RUN =====
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
