import stripe
import datetime
import os
import asyncio
from flask import Flask, request
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
# PROCESSAR USUÁRIO
# ==================================================

async def process_user(user_id, plan):

    try:

        # link expira em 5 minutos
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        # ==================================================
        # DAILY = SOMENTE GRUPO DE FOTOS
        # ==================================================

        if plan == "daily":

            invite = await bot.create_chat_invite_link(
                chat_id=GROUP_FOTOS,
                expire_date=expire,
                member_limit=1
            )

            message = f"""
✅ Payment Confirmed

🔥 Welcome inside

📸 DAILY ACCESS:
{invite.invite_link}

⚠️ This link expires in 5 minutes.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

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
        # MONTHLY / LIFETIME = GRUPO PREMIUM
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

🔥 Premium Photos & Videos:
{invite.invite_link}

⚠️ This link expires in 5 minutes.
"""

            await bot.send_message(
                chat_id=user_id,
                text=message
            )

        print("Mensagem enviada com sucesso")

    except Exception as e:
        print("ERRO PROCESS_USER:", e)

# ==================================================
# CHECKOUT
# ==================================================

@app.route("/create-checkout/<plan>/<user_id>")
def create_checkout(plan, user_id):

    try:

        session = stripe.checkout.Session.create(

            payment_method_types=["card"],

            line_items=[{
                "price": PLANS[plan],
                "quantity": 1,
            }],

            mode="payment",

            # IMPORTANTE
            client_reference_id=user_id,

            metadata={
                "plan": plan
            },

            success_url="https://SEU-APP.up.railway.app/success",

            cancel_url="https://t.me/SEU_BOT"
        )

        return {
            "url": session.url
        }

    except Exception as e:

        print("ERRO CHECKOUT:", e)

        return {
            "error": str(e)
        }

# ==================================================
# PÁGINA DE SUCESSO
# ==================================================

@app.route("/success")
def success():

    return """
    <html>

    <head>

        <meta http-equiv="refresh" content="3;url=https://t.me/SEU_BOT">

    </head>

    <body style="background:black;color:white;text-align:center;padding-top:100px;font-family:sans-serif;">

        <h1>✅ Payment Successful</h1>

        <p>Your VIP access is being prepared...</p>

        <p>Returning to Telegram...</p>

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
