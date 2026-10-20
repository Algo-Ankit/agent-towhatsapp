"""Stand-in inventory agent.

Two ways to use your real inventory agent:
  1. It runs as a service: set INVENTORY_AGENT_URL in .env (no code change, see README).
  2. It is Python code: replace `handle` and `confirm` below with calls into it.
Contract:
  handle(vendor, text) -> AgentResult
  confirm(vendor, action, payload) -> str   (runs after the vendor replies YES)
"""
import re

from .. import db
from .base import AgentResult


def _list(vendor_id):
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM inventory WHERE vendor_id=? ORDER BY sku", (vendor_id,)
        ).fetchall()
    if not rows:
        return "No products yet."
    lines = [f"{r['sku']}: {r['name']} | qty {r['qty']} | Rs {r['price']:.0f}" for r in rows]
    low = [r["sku"] for r in rows if r["qty"] < 10]
    out = "Your stock:\n" + "\n".join(lines)
    if low:
        out += f"\n\nLow stock: {', '.join(low)}"
    return out


def execute(vendor_id: str, action: str, payload: dict) -> str:
    """Actually apply a change. Called directly for safe actions, or after YES for risky ones."""
    sku = payload["sku"]
    with db.conn() as c:
        row = c.execute(
            "SELECT * FROM inventory WHERE vendor_id=? AND sku=?", (vendor_id, sku)
        ).fetchone()
        if not row:
            return f"SKU {sku} not found. Send 'stock' to see your products."
        if action == "add_qty":
            c.execute(
                "UPDATE inventory SET qty=qty+? WHERE vendor_id=? AND sku=?",
                (payload["n"], vendor_id, sku),
            )
            return f"Added {payload['n']} to {sku}. New qty: {row['qty'] + payload['n']}"
        if action == "set_qty":
            c.execute(
                "UPDATE inventory SET qty=? WHERE vendor_id=? AND sku=?",
                (payload["n"], vendor_id, sku),
            )
            return f"{sku} qty set to {payload['n']}"
        if action == "set_price":
            c.execute(
                "UPDATE inventory SET price=? WHERE vendor_id=? AND sku=?",
                (payload["price"], vendor_id, sku),
            )
            return f"{sku} price changed from Rs {row['price']:.0f} to Rs {payload['price']:.0f}"
    return "Unknown action."


def handle(vendor: dict, text: str) -> AgentResult:
    t = text.strip().lower()
    vid = vendor["id"]

    if t in {"stock", "inventory", "list", "show stock"}:
        return AgentResult(reply=_list(vid))

    # "add 20 RICE5"  -> safe, run immediately
    m = re.match(r"add\s+(\d+)\s+(\w+)", t)
    if m:
        return AgentResult(reply=execute(vid, "add_qty", {"n": int(m[1]), "sku": m[2].upper()}))

    # "set RICE5 qty 0" -> risky, needs confirmation
    m = re.match(r"set\s+(\w+)\s+qty\s+(\d+)", t)
    if m:
        p = {"sku": m[1].upper(), "n": int(m[2])}
        return AgentResult(
            reply=f"Set {p['sku']} quantity to {p['n']}? Reply YES to confirm.",
            pending=("set_qty", p),
        )

    # "price RICE5 499" -> risky, needs confirmation
    m = re.match(r"price\s+(\w+)\s+(\d+(?:\.\d+)?)", t)
    if m:
        p = {"sku": m[1].upper(), "price": float(m[2])}
        return AgentResult(
            reply=f"Change {p['sku']} price to Rs {p['price']:.0f}? Reply YES to confirm.",
            pending=("set_price", p),
        )

    return AgentResult(
        reply="I can do: 'stock', 'add 20 RICE5', 'set RICE5 qty 0', 'price RICE5 499'."
    )


def confirm(vendor: dict, action: str, payload: dict) -> str:
    return execute(vendor["id"], action, payload)
