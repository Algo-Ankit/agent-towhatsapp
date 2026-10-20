"""Decides what happens to each vendor message: link, confirm, or route to an agent.

Routing is keyword based so the demo works with no API keys.
For production, swap `pick_agent` for an LLM classifier or one orchestrator agent
that calls inventory/support as tools.
"""
import json

from . import db
from .agents import AGENTS

INVENTORY_WORDS = (
    "stock", "inventory", "add ", "set ", "price ", "qty", "quantity",
    "list", "sku", "restock", "product", "item",
)
YES = {"YES", "Y", "HAAN", "HA", "HAN", "OK CONFIRM"}
NO = {"NO", "N", "CANCEL", "NAHI"}


def pick_agent(text: str) -> str:
    t = text.lower()
    return "inventory" if any(w in t for w in INVENTORY_WORDS) else "support"


def handle_message(phone: str, text: str) -> str:
    text = (text or "").strip()
    vendor = db.vendor_by_phone(phone)

    # 1. Unknown number: only allow linking
    if not vendor:
        parts = text.split()
        if len(parts) == 2 and parts[0].upper() == "LINK":
            v = db.link_vendor(phone, parts[1])
            if v:
                return f"Linked to {v['name']}. Send 'stock' to see your inventory."
            return "That code is not valid. Check the code on your vendor dashboard."
        return "This number is not linked to a vendor account. Send: LINK <your-code>"

    vendor = dict(vendor)

    # 2. Confirmation for a pending risky action
    if text.upper() in YES:
        pending = db.pop_pending(phone)
        if not pending:
            return "Nothing waiting for confirmation."
        agent_name, action = pending["action"].split(":", 1)
        return AGENTS[agent_name].confirm(vendor, action, json.loads(pending["payload"]))
    if text.upper() in NO:
        db.pop_pending(phone)
        return "Cancelled."

    # 3. Route to an agent
    name = pick_agent(text)
    result = AGENTS[name].handle(vendor, text)
    if result.pending:
        action, payload = result.pending
        db.set_pending(phone, f"{name}:{action}", json.dumps(payload))
    return result.reply
