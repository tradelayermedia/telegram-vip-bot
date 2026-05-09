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

# 📸 Grupo DAILY (somente fotos)
GROUP_FOTOS = int(os.getenv("GROUP_FOTOS"))

# 👑 Grupo PREMIUM (fotos + vídeos)
GROUP_PREMIUM = int(os.getenv("GROUP_PREMIUM"))

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# ==================================================
# LINKS
# ==================================================

# 🔥 URL DO RAILWAY
BASE_URL = os.getenv("BASE_URL")

# 🔥 LINK DO BOT
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
# APP
# ==================================================

bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)

# ==================================================
# PROCESS USER
# ==================================================

async def process_user(user_id, plan):

    try:

        # link expira em 5 minutos
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        # ==================================================
        # DAILY
        # ==================================================

        if plan == "daily":

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
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

            print("Link DAILY enviado")

            # ==================================================
            # TESTE: REMOVE APÓS 1 MINUTO
            # ==================================================

            await asyncio.sleep(60)

            try:

                await bot.ban_chat_member(
                    chat_id=GROUP_FOTOS,
                    user_id=user_id
                )

                await bot.unban_chat_member(
                    chat_id=GROUP_FOTOS,
                    user_id=user_id
                )

                print(f"Usuário {user_id} removido do DAILY")

            except Exception as e:

                print("ERRO AO REMOVER:", e)

        # ==================================================
        # MONTHLY / LIFETIME
        # ==================================================

        elif plan in ["monthly", "lifetime"]:

            invite = await bot.create_chat_invite_link(
                chat_id=GROUP_PREMIUM,
                expire_date=expire,
                member_limit=1
            )

            message = f"""
✅ Payment Confirmed

👑 VIP ACCESS UNLOCKED

🔥 Join your premium group:
{invite.invite_link}

⚠️ This invite expires in 5 minutes.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

            print("Link PREMIUM enviado")

    except Exception as e:

        print("ERRO PROCESS_USER:", e)

# ==================================================
# CREATE CHECKOUT
# ==================================================

@app.route("/create-checkout/<plan>/<user_id>")
def create_checkout(plan, user_id):

    try:

        session = stripe.checkout.Session.create(

            payment_method_types=[
                "card"
            ],

            line_items=[{
                "price": PLANS[plan],
                "quantity": 1,
            }],

            mode="payment",

            client_reference_id=user_id,

            metadata={
                "plan": plan
            },

            # 🔥 SUCCESS PAGE
            success_url=f"{BASE_URL}/success",

            # 🔥 CANCEL
            cancel_url=BOT_LINK
        )

        # 🔥 REDIRECIONA DIRETO PARA O CHECKOUT
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

        print("Webhook error:", e)

        return "error", 400

    # ==================================================
    # PAGAMENTO APROVADO
    # ==================================================

    if event["type"] == "checkout.session.completed":

        print("Webhook recebido: checkout.session.completed")

        session = event["data"]["object"]

        user_id = int(session["client_reference_id"])

        plan = session["metadata"]["plan"]

        print("Pagamento confirmado para:", user_id)
        print("Plano:", plan)

        asyncio.run(
            process_user(user_id, plan)
        )

    return "OK"

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=3000
    )
