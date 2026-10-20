"""Template: wrap an existing agent so the WhatsApp bridge can call it over HTTP.

Give this file to whoever owns the agents. They replace the two TODO blocks with
calls into their real agent, run it, and put the URL in the bridge's .env:

    uvicorn examples.agent_server_template:app --port 9001
    INVENTORY_AGENT_URL=http://localhost:9001/inventory
    SUPPORT_AGENT_URL=http://localhost:9001/support

Request JSON (from the bridge):
    {"type": "message", "vendor_id": "v_001", "vendor_name": "...", "phone": "91...", "message": "price RICE5 499"}
    {"type": "confirm", "vendor_id": "v_001", ..., "action": "set_price", "payload": {...}}   # after vendor says YES

Response JSON (to the bridge):
    {"reply": "text sent to vendor on WhatsApp"}
    {"reply": "Change price to 499? Reply YES", "pending": {"action": "set_price", "payload": {...}}}
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Agent server template")


class AgentRequest(BaseModel):
    type: str  # "message" or "confirm"
    vendor_id: str
    vendor_name: str = ""
    phone: str = ""
    message: str = ""
    action: str = ""
    payload: dict = {}


@app.post("/inventory")
def inventory(req: AgentRequest):
    if req.type == "confirm":
        # TODO: actually apply req.action with req.payload for req.vendor_id
        return {"reply": f"[inventory agent] done: {req.action} {req.payload}"}

    # TODO: call your real inventory agent here, e.g.
    #   out = inventory_agent.run(req.message, vendor_id=req.vendor_id)
    msg = req.message.lower()
    if msg.startswith("price"):
        _, sku, price = msg.split()
        return {
            "reply": f"[inventory agent] Change {sku.upper()} price to Rs {price}? Reply YES",
            "pending": {"action": "set_price", "payload": {"sku": sku.upper(), "price": float(price)}},
        }
    return {"reply": f"[inventory agent] got '{req.message}' for vendor {req.vendor_id}"}


@app.post("/support")
def support(req: AgentRequest):
    # TODO: call your real support agent here
    return {"reply": f"[support agent] got '{req.message}' for vendor {req.vendor_id}"}
