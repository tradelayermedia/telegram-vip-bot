import stripe
import datetime
import os
import asyncio

from flask import Flask, request, redirect
from telegram import Bot

# ==================================================
# CONFIG
# ==================================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📸 DAILY (somente fotos)
GROUP_FOTOS = int(os.getenv("GROUP_FOTOS"))

# 👑 PREMIUM (fotos + vídeos)
GROUP_PREMIUM = int(os.getenv("GROUP_PREMIUM"))

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# ==================================================
# LINKS
# ==================================================

BASE_URL = os.getenv("BASE_URL")

BOT_LINK = os.getenv("BOT_LINK")

# ==================================================
# PRICE IDS
# ==================================================

PLANS = {
    "daily": os.getenv("PRICE_DAILY"),
    "monthly": os.getenv("PRICE_MONTHLY"),
    "lifetime": os.getenv("PRICE_LIFETIME")
}

# ==================================================
# TEMPOS
# ==================================================

# 24 horas
DAILY_TIME = 86400

# 30 dias
MONTHLY_TIME = 2592000

# ==================================================
# APP
# ==================================================

bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)

# ==================================================
# REMOVER USUÁRIO
# ==================================================

async def remove_user(group_id, user_id):

    try:

        await bot.ban_chat_member(
            chat_id=group_id,
            user_id=user_id
        )

        await bot.unban_chat_member(
            chat_id=group_id,
            user_id=user_id
        )

        print(f"USUÁRIO {user_id} REMOVIDO")

    except Exception as e:

        print("ERRO AO REMOVER:", e)

# ==================================================
# PROCESS USER
# ==================================================

async def process_user(user_id, plan):

    try:

        print(f"PROCESSANDO USUÁRIO {user_id}")
        print(f"PLANO: {plan}")

        # link expira em 5 minutos
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        # ==================================================
        # DAILY
        # ==================================================

        if plan == "daily":

            print("ENTRANDO NO DAILY")

            invite = await bot.create_chat_invite_link(
                chat_id=GROUP_FOTOS,
                expire_date=expire,
                member_limit=1
            )

            message = f"""
✅ Payment Confirmed

🔥 DAILY ACCESS UNLOCKED

📸 Join here:
{invite.invite_link}

⚠️ This invite expires in 5 minutes.
⚠️ Access duration: 24 hours.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

            print("LINK DAILY ENVIADO")

            # ==================================================
            # REMOVE APÓS 24 HORAS
            # ==================================================

            await asyncio.sleep(DAILY_TIME)

            await remove_user(
                GROUP_FOTOS,
                user_id
            )

        # ==================================================
        # MONTHLY
        # ==================================================

        elif plan == "monthly":

            print("ENTRANDO NO MONTHLY")

            invite = await bot.create_chat_invite_link(
                chat_id=GROUP_PREMIUM,
                expire_date=expire,
                member_limit=1
            )

            message = f"""
✅ Payment Confirmed

🔥 MONTHLY VIP UNLOCKED

👑 Join here:
{invite.invite_link}

⚠️ This invite expires in 5 minutes.
⚠️ Access duration: 30 days.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

            print("LINK MONTHLY ENVIADO")

            # ==================================================
            # REMOVE APÓS 30 DIAS
            # ==================================================

            await asyncio.sleep(MONTHLY_TIME)

            await remove_user(
                GROUP_PREMIUM,
                user_id
            )

        # ==================================================
        # LIFETIME
        # ==================================================

        elif plan == "lifetime":

            print("ENTRANDO NO LIFETIME")

            invite = await bot.create_chat_invite_link(
                chat_id=GROUP_PREMIUM,
                expire_date=expire,
                member_limit=1
            )

            message = f"""
✅ Payment Confirmed

👑 LIFETIME ACCESS UNLOCKED

🔥 Join here:
{invite.invite_link}

♾ Permanent VIP access granted.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

            print("LINK LIFETIME ENVIADO")

        # ==================================================
        # INVALID PLAN
        # ==================================================

        else:

            print("PLANO INVÁLIDO:", plan)

    except Exception as e:

        print("ERRO PROCESS_USER:", e)

# ==================================================
# CREATE CHECKOUT
# ==================================================

@app.route("/create-checkout/<plan>/<user_id>")
def create_checkout(plan, user_id):

    try:

        print("CRIANDO CHECKOUT")
        print("PLANO:", plan)
        print("USUÁRIO:", user_id)

        session = stripe.checkout.Session.create(

            payment_method_types=[
                "card"
            ],

            line_items=[{
                "price": PLANS[plan],
                "quantity": 1,
            }],

            mode="payment",

            metadata={
                "plan": str(plan),
                "user_id": str(user_id)
            },

            success_url=f"{BASE_URL}/success",

            cancel_url=BOT_LINK
        )

        print("CHECKOUT CRIADO")

        return redirect(session.url)

    except Exception as e:

        print("ERRO CHECKOUT:", e)

        return {
            "error": str(e)
        }

# ==================================================
# SUCCESS PAGE
# ==================================================

@app.route("/success")
def success():

    return f"""
    <html>

    <head>

        <meta http-equiv="refresh" content="4;url={BOT_LINK}">

        <title>VIP Access</title>

    </head>

    <body style="
        background:#000;
        color:white;
        font-family:sans-serif;
        text-align:center;
        padding-top:100px;
    ">

        <h1 style="font-size:48px;">
            🔥 VIP ACCESS UNLOCKED
        </h1>

        <p style="font-size:22px;">
            Your private content is waiting...
        </p>

        <p style="margin-top:30px;font-size:18px;color:#aaa;">
            Returning to Telegram...
        </p>

    </body>

    </html>
    """

# ==================================================
# WEBHOOK
# ==================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.data

    sig_header = request.headers.get("stripe-signature")

    try:

        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            WEBHOOK_SECRET
        )

    except Exception as e:

        print("WEBHOOK ERROR:", e)

        return "error", 400

    # ==================================================
    # PAYMENT SUCCESS
    # ==================================================

    if event["type"] == "checkout.session.completed":

        print("WEBHOOK RECEBIDO: checkout.session.completed")

        session = event["data"]["object"]

        print(session)

        try:

            user_id = int(session["metadata"]["user_id"])

            plan = str(
                session["metadata"]["plan"]
            ).lower()

            print("USER RECEBIDO:", user_id)
            print("PLAN RECEBIDO:", plan)

            asyncio.run(
                process_user(user_id, plan)
            )

        except Exception as e:

            print("ERRO PROCESSANDO WEBHOOK:", e)

    return "OK"

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=3000
    )
