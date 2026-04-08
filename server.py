import stripe
import datetime
import os
from flask import Flask, request
from telegram import Bot

# ===== CONFIG =====
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# 🔴 PRICE IDS via variável
PRICE_DAILY = os.getenv("PRICE_DAILY")
PRICE_MONTHLY = os.getenv("PRICE_MONTHLY")
PRICE_LIFETIME = os.getenv("PRICE_LIFETIME")

PLANS = {
    "daily": PRICE_DAILY,
    "monthly": PRICE_MONTHLY,
    "lifetime": PRICE_LIFETIME
}

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

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
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = int(session["client_reference_id"])

        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

        invite_link = bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            expire_date=expire,
            member_limit=1
        )

        bot.send_message(
            chat_id=user_id,
            text="✅ Payment confirmed!\n\n🔥 Your VIP access:\n" + invite_link.invite_link
        )

    return "OK"

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
