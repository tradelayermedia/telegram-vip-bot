import stripe
import datetime
import os
import asyncio
from flask import Flask, request
from telegram import Bot

# ===== CONFIG =====
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

PLANS = {
    "daily": os.getenv("PRICE_DAILY"),
    "monthly": os.getenv("PRICE_MONTHLY"),
    "lifetime": os.getenv("PRICE_LIFETIME")
}

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ===== FUNÇÃO ASYNC PRINCIPAL =====
async def process_user(user_id):
    try:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        invite_link = await bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            expire_date=expire,
            member_limit=1
        )

        print("Link criado:", invite_link.invite_link)

        await bot.send_message(
            chat_id=user_id,
            text="✅ Payment confirmed!\n\n🔥 Your VIP access (1 minute test):\n" + invite_link.invite_link
        )

        print("Mensagem enviada para:", user_id)

        # espera 1 minuto
        await asyncio.sleep(60)

        try:
            await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            print(f"Usuário {user_id} removido")
        except Exception as e:
            print("ERRO AO REMOVER:", str(e))

    except Exception as e:
        print("ERRO GERAL:", str(e))

# ===== CHECKOUT =====
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
            success_url="https://t.me/",
            cancel_url="https://t.me/",
            client_reference_id=user_id
        )

        return {"url": session.url}

    except Exception as e:
        print("ERRO CHECKOUT:", str(e))
        return {"error": str(e)}

# ===== WEBHOOK =====
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        print("Webhook:", event["type"])

    except Exception as e:
        print("ERRO WEBHOOK:", str(e))
        return "erro", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["client_reference_id"])

        print("Pagamento confirmado:", user_id)

        # 🔥 EXECUTA TUDO EM UM ÚNICO LOOP
        asyncio.run(process_user(user_id))

    return "OK"

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
