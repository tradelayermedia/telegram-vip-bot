{\rtf1\ansi\ansicpg1252\cocoartf2869
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\froman\fcharset0 Times-Roman;\f2\fnil\fcharset0 AppleColorEmoji;
}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup\
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes\
import requests\
\
# ===== CONFIG =====\
BOT_TOKEN = 
\f1 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 "BOT_TOKEN")
\f0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0   # 
\f2 \uc0\u55357 \u56628 
\f0  COLOQUE SEU TOKEN\
BASE_URL = "https://SEU-APP.up.railway.app"  # 
\f2 \uc0\u55357 \u56628 
\f0  COLOQUE SUA URL DO RAILWAY\
\
# ===== START =====\
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    keyboard = [\
        [InlineKeyboardButton("
\f2 \uc0\u55357 \u56462 
\f0  Daily - $2.99", callback_data="daily")],\
        [InlineKeyboardButton("
\f2 \uc0\u55357 \u56462 
\f0  Monthly - $12.99", callback_data="monthly")],\
        [InlineKeyboardButton("
\f2 \uc0\u55357 \u56462 
\f0  Lifetime - $39.99", callback_data="lifetime")]\
    ]\
\
    reply_markup = InlineKeyboardMarkup(keyboard)\
\
    await update.message.reply_text(\
        "
\f2 \uc0\u55357 \u56613 
\f0  VIP ACCESS 
\f2 \uc0\u55357 \u56613 
\f0 \\n\\n"\
        "Exclusive content available.\\n\\n"\
        "Choose your plan:",\
        reply_markup=reply_markup\
    )\
\
# ===== CLICK NOS BOT\'d5ES =====\
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
\
    user_id = query.from_user.id\
    plan = query.data\
\
    try:\
        # chama seu servidor (Railway)\
        response = requests.get(f"\{BASE_URL\}/create-checkout/\{plan\}/\{user_id\}")\
        data = response.json()\
\
        payment_url = data.get("url")\
\
        await query.message.reply_text(\
            f"
\f2 \uc0\u55357 \u56499 
\f0  Complete your payment below:\\n\\n\{payment_url\}\\n\\n"\
            "
\f2 \uc0\u9889 
\f0  After payment, you will receive access automatically."\
        )\
\
    except Exception as e:\
        await query.message.reply_text(\
            "
\f2 \uc0\u10060 
\f0  Error generating payment link. Try again later."\
        )\
        print(e)\
\
# ===== RUN =====\
app = ApplicationBuilder().token(BOT_TOKEN).build()\
\
app.add_handler(CommandHandler("start", start))\
app.add_handler(CallbackQueryHandler(button_handler))\
\
print("Bot is running...")\
app.run_polling()}