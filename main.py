from flask import Flask, request, jsonify
import stripe
import json
import requests

app = Flask(__name__)

# Load config.json
with open("config.json", "r") as f:
    config = json.load(f)

# Your Stripe secret key
stripe.api_key = "sk_live_REPLACE_THIS"

# Your webhook secret from Stripe dashboard
STRIPE_WEBHOOK_SECRET = "whsec_REPLACE_THIS"

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        product_id = session["metadata"].get("product_id")

        if not product_id:
            return "No product ID", 400

        shelly_info = config.get(product_id)
        if not shelly_info:
            return "Unknown product ID", 404

        ip = shelly_info["ip"]
        duration = shelly_info.get("duration_ms", 500) / 1000

        try:
            requests.get(f"http://{ip}/relay/0?turn=on&timer={duration}")
            print(f"✅ Triggered Shelly at {ip} for product {product_id}")
        except Exception as e:
            print(f"❌ Failed to trigger Shelly: {e}")
            return "Shelly trigger error", 500

    return "OK", 200