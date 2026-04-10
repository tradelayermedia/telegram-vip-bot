import stripe
import datetime
import os
import threading
from flask import Flask, request
from telegram import Bot

# ===== CONFIG =====
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# PRICE IDs
PLANS = {
    "daily": os.getenv("PRICE_DAILY"),
    "monthly": os.getenv("PRICE_MONTHLY"),
    "lifetime": os.getenv("PRICE_LIFETIME")
}

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ===== CHECKOUT =====
@app.route("/create-checkout/<plan>/<user_id>")
def create_checkout(plan, user_id):
    try:
        print(f"Criando checkout: {plan} | user {user_id}")

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

        print("Checkout criado com sucesso")
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
        print("Webhook recebido:", event["type"])

    except Exception as e:
        print("ERRO WEBHOOK:", str(e))
        return "erro", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = int(session["client_reference_id"])
        print("Pagamento confirmado para:", user_id)

        try:
            # cria link único
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

            invite_link = bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                expire_date=expire,
                member_limit=1
            )

            print("Link criado:", invite_link.invite_link)

        except Exception as e:
            print("ERRO AO CRIAR LINK:", str(e))
            return "erro ao criar link", 500

        try:
            # envia mensagem
            bot.send_message(
                chat_id=user_id,
                text="✅ Payment confirmed!\n\n🔥 Your VIP access (1 minute test):\n" + invite_link.invite_link
            )

            print("Mensagem enviada para:", user_id)

        except Exception as e:
            print("ERRO AO ENVIAR MSG:", str(e))

        # ===== REMOVER APÓS 1 MINUTO =====
        def remove_user():
            try:
                bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                print(f"Usuário {user_id} removido após 1 minuto")
            except Exception as e:
                print("ERRO AO REMOVER:", str(e))

        threading.Timer(60, remove_user).start()

    return "OK"

# ===== RUN =====
if __name__ == "__main__":
    print("Servidor rodando...")
    app.run(host="0.0.0.0", port=3000)
