"""Everything that talks to Meta's WhatsApp Cloud API lives here."""
import hashlib
import hmac

import httpx

from . import config


def signature_ok(raw_body: bytes, header: str | None) -> bool:
    """Check X-Hub-Signature-256 so nobody can fake vendor messages."""
    if not config.WA_APP_SECRET:
        return config.DRY_RUN  # allow unsigned only in local dry-run mode
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(config.WA_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def extract_messages(payload: dict):
    """Yield (wamid, from_phone, type, text) for each inbound message in a webhook payload.
    Status updates (sent/delivered/read) are ignored."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for m in value.get("messages", []):
                mtype = m.get("type")
                text = ""
                if mtype == "text":
                    text = m["text"]["body"]
                elif mtype == "interactive":  # button / list replies
                    inter = m["interactive"]
                    text = (inter.get("button_reply") or inter.get("list_reply") or {}).get("title", "")
                elif mtype == "button":
                    text = m["button"].get("text", "")
                yield m["id"], m["from"], mtype, text


async def send_text(to: str, body: str):
    if config.DRY_RUN:
        print(f"\n[DRY_RUN reply -> {to}]\n{body}\n")
        return
    url = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}/{config.WA_PHONE_NUMBER_ID}/messages"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            url,
            headers={"Authorization": f"Bearer {config.WA_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body[:4096]},
            },
        )
        if r.status_code >= 300:
            print("WhatsApp send failed:", r.status_code, r.text)
