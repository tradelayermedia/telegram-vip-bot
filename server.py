{\rtf1\ansi\ansicpg1252\cocoartf2869
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\froman\fcharset0 Times-Roman;\f2\fnil\fcharset0 AppleColorEmoji;
\f3\fnil\fcharset0 HelveticaNeue;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;\red20\green32\blue52;\red255\green255\blue255;
}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;\cssrgb\c10196\c17255\c26667;\cssrgb\c100000\c100000\c100000;
}
\paperw11900\paperh16840\margl1440\margr1440\vieww29200\viewh15460\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import stripe\
import datetime\
import os\
from flask import Flask, request\
from telegram import Bot\
\
# ===== CONFIGURA\'c7\'d5ES =====\
\
\pard\pardeftab720\partightenfactor0

\f1 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
\f0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0  # 
\f2 \uc0\u55357 \u56628 
\f0  COLOQUE SUA SECRET KEY DO STRIPE\
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0
\cf0 \
\pard\pardeftab720\partightenfactor0

\f1 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 BOT_TOKEN = os.getenv("BOT_TOKEN")\
GROUP_ID = int(os.getenv("GROUP_ID"))\
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
\f0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 \
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0
\cf0 \
bot = Bot(token=BOT_TOKEN)\
app = Flask(__name__)\
\
# ===== PLANOS =====\
PLANS = \{\
    "daily": "
\f3\fs28 \cf3 \cb4 \expnd0\expndtw0\kerning0
price_1THDnKRylXPx9kEqd3PCShw4
\f0\fs24 \cf0 \cb1 \kerning1\expnd0\expndtw0 ",       # 
\f2 \uc0\u55357 \u56628 
\f0  EX: price_123\
    "monthly": "
\f3\fs28 \cf3 \cb4 \expnd0\expndtw0\kerning0
price_1THDo7RylXPx9kEqGUgYdVL0
\f0\fs24 \cf0 \cb1 \kerning1\expnd0\expndtw0 ",   # 
\f2 \uc0\u55357 \u56628 
\f0  EX: price_123\
    "lifetime": "
\f3\fs28 \cf3 \cb4 \expnd0\expndtw0\kerning0
price_1THDpNRylXPx9kEqLi8YFDwx
\f0\fs24 \cf0 \cb1 \kerning1\expnd0\expndtw0 "  # 
\f2 \uc0\u55357 \u56628 
\f0  EX: price_123\
\}\
\
# ===== CRIAR PAGAMENTO =====\
@app.route("/create-checkout/<plan>/<user_id>")\
def create_checkout(plan, user_id):\
\
    session = stripe.checkout.Session.create(\
        payment_method_types=['card'],\
        line_items=[\{\
            'price': PLANS[plan],\
            'quantity': 1,\
        \}],\
        mode='payment',\
        success_url='https://t.me/',  # pode deixar assim\
        cancel_url='https://t.me/',\
        client_reference_id=user_id\
    )\
\
    return \{"url": session.url\}\
\
# ===== WEBHOOK (CONFIRMA PAGAMENTO) =====\
@app.route("/webhook", methods=["POST"])\
def webhook():\
    payload = request.data\
    sig_header = request.headers.get("stripe-signature")\
\
    event = stripe.Webhook.construct_event(\
        payload, sig_header, WEBHOOK_SECRET\
    )\
\
    if event["type"] == "checkout.session.completed":\
        session = event["data"]["object"]\
\
        user_id = int(session["client_reference_id"])\
\
        # cria link \'fanico do telegram\
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)\
\
        invite_link = bot.create_chat_invite_link(\
            chat_id=GROUP_ID,\
            expire_date=expire,\
            member_limit=1\
        )\
\
        bot.send_message(\
            chat_id=user_id,\
            text=f"
\f2 \uc0\u9989 
\f0  Payment confirmed!\\n\\n
\f2 \uc0\u55357 \u56613 
\f0  Your VIP access:\\n\{invite_link.invite_link\}"\
        )\
\
    return "OK"\
\
# ===== RODAR SERVIDOR =====\
app.run(host="0.0.0.0", port=3000)}