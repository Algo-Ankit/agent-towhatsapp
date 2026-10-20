"""Pretend to be a vendor on WhatsApp without needing Meta.

Sends a payload shaped exactly like Meta's webhook to your local server.
Run the server with DRY_RUN=1 and watch replies print in the server terminal.

Usage:
  python scripts/simulate.py                      # interactive chat
  python scripts/simulate.py "LINK SHARMA42" stock "add 10 OIL1"
"""
import hashlib
import hmac
import json
import os
import sys
import time
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("SIM_URL", "http://localhost:8000/webhook")
PHONE = os.getenv("SIM_PHONE", "919812345678")
SECRET = os.getenv("WA_APP_SECRET", "")


def payload(text):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550000000", "phone_number_id": "PNID"},
                    "contacts": [{"profile": {"name": "Demo Vendor"}, "wa_id": PHONE}],
                    "messages": [{
                        "from": PHONE,
                        "id": f"wamid.{uuid.uuid4().hex}",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": text},
                    }],
                },
            }],
        }],
    }


def send(text, echo=True):
    body = json.dumps(payload(text)).encode()
    headers = {"Content-Type": "application/json"}
    if SECRET:
        headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    try:
        r = httpx.post(URL, content=body, headers=headers, timeout=10)
    except httpx.ConnectError:
        print(f"\n  Server is not running at {URL}.")
        print("  Start it in another terminal:  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("  Or run everything in one go:   bash scripts/demo.sh\n")
        return
    if echo:
        print(f"vendor> {text}")
    if r.status_code != 200:
        print(f"  (server answered {r.status_code}: {r.text})")
    time.sleep(0.6)  # give the agent time to print its reply before the next prompt


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for msg in sys.argv[1:]:
            send(msg)
    else:
        print(f"You are a vendor messaging from WhatsApp number +{PHONE} (fake, for testing).")
        print("Agent replies show as 'agent ->'. They are printed here instead of sent, until Meta is connected.")
        print("Ctrl+C to quit.\n")
        try:
            while True:
                msg = input("vendor> ").strip()
                if msg:
                    send(msg, echo=False)
        except (KeyboardInterrupt, EOFError):
            print("\nbye")
