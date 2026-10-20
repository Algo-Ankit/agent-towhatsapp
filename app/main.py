"""WhatsApp <-> agents bridge.

GET  /webhook  Meta's one-time verification handshake
POST /webhook  every inbound WhatsApp message lands here
"""
import asyncio
import json

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from . import config, db, whatsapp
from .agents import describe as describe_agents
from .router import handle_message

app = FastAPI(title="WhatsApp Agent Bridge")


@app.on_event("startup")
def _startup():
    db.init_db()
    mode = "DRY_RUN (replies printed, not sent)" if config.DRY_RUN else "LIVE (sending via Meta)"
    print(f"Bridge started in {mode}")
    print(f"Agents: {describe_agents()}")


@app.get("/health")
def health():
    return {"ok": True, "dry_run": config.DRY_RUN, "agents": describe_agents()}


@app.get("/webhook")
def verify(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    if mode == "subscribe" and token == config.WA_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification failed")


async def process(phone: str, text: str):
    # Agents may be slow (LLM calls), so run them off the request path
    reply = await asyncio.to_thread(handle_message, phone, text)
    await whatsapp.send_text(phone, reply)


@app.post("/webhook")
async def inbound(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not whatsapp.signature_ok(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="bad signature")

    payload = json.loads(raw or b"{}")
    for wamid, phone, mtype, text in whatsapp.extract_messages(payload):
        if db.already_processed(wamid):
            continue  # Meta retry, already handled
        if mtype in {"audio", "image", "document", "video"} and not text:
            # TODO: download media via Graph API, transcribe voice notes, then route
            background.add_task(
                whatsapp.send_text, phone, "Got your media. Voice and image support is coming soon; please type for now."
            )
            continue
        background.add_task(process, phone, text)

    # Always answer fast so Meta does not retry
    return {"status": "received"}
