# WhatsApp Agent Bridge

Vendors message one WhatsApp business number. This server receives each message, identifies the vendor by phone number, routes it to the inventory or support agent, and replies on WhatsApp.

```
Vendor's WhatsApp -> your business number -> Meta -> POST /webhook
  -> vendor lookup -> router -> inventory / support agent -> reply via Graph API
```

## Project layout

| File | What it does |
|---|---|
| `app/main.py` | Webhook endpoints (verify + receive), fast 200, background processing |
| `app/whatsapp.py` | Signature check, payload parsing, sending replies |
| `app/router.py` | Vendor linking, YES/NO confirmations, picks the agent |
| `app/agents/inventory.py` | **Stand-in. Replace `handle()` with your real inventory agent** |
| `app/agents/support.py` | **Stand-in. Replace `handle()` with your real support agent** |
| `app/db.py` | SQLite: vendors, inventory, dedupe, pending confirmations |
| `scripts/simulate.py` | Fake vendor chat, no Meta needed |

## 1. Run locally or in Codespaces (no Meta account needed)

Codespaces: push this folder to a GitHub repo, then **Code > Codespaces > Create codespace**. Dependencies install automatically.

```bash
pip install -r requirements.txt   # skip in Codespaces
cp .env.example .env              # skip in Codespaces
uvicorn app.main:app --port 8000  # terminal 1
python scripts/simulate.py "LINK SHARMA42" stock "add 10 OIL1" "price RICE5 499" YES   # terminal 2
```

Replies print in terminal 1. Run `python scripts/simulate.py` with no arguments for an interactive chat.

Demo commands: `LINK SHARMA42` (link number to the seeded vendor), `stock`, `add 20 RICE5`, `set RICE5 qty 0`, `price RICE5 499`, `YES` / `NO`, anything about payouts or orders goes to support.

## 2. Connect real WhatsApp

1. **Meta app**: developers.facebook.com > Create app > Business type > add the **WhatsApp** product.
2. **API Setup** page: copy the temporary access token and **Phone number ID** into `.env`. Add your own phone under "To" as a test recipient (test numbers allow up to 5).
3. **App secret**: App settings > Basic > App secret, put in `.env` as `WA_APP_SECRET`.
4. Set `DRY_RUN=0` in `.env` and restart the server.
5. **Public URL**:
   - Codespaces: Ports tab > port 8000 > right click > **Port Visibility > Public**. Copy the forwarded URL.
   - Local: `ngrok http 8000`.
6. **Webhook**: WhatsApp > Configuration > Webhook > Edit. Callback URL `https://<your-url>/webhook`, Verify token = `WA_VERIFY_TOKEN` from `.env`. Verify and save, then **Subscribe** to the `messages` field.
7. From your phone, message the test number: `LINK SHARMA42`, then `stock`.

## 3. Plug in your real agents

Your agents only need to follow this contract:

```python
def handle(vendor: dict, text: str) -> AgentResult:
    # vendor = {"id": "v_001", "name": "...", "phone": "..."}
    # return AgentResult(reply="text for vendor")
    # or, for a change that needs confirmation:
    # return AgentResult(reply="Change X? Reply YES", pending=("action_name", json_payload))
```

If your agents run as a separate service (Azure AI Foundry, LangGraph server, etc.), make `handle()` an HTTP call to it and pass `vendor["id"]` so the agent can only touch that vendor's data. Swap `pick_agent()` in `router.py` for an LLM classifier or a single orchestrator agent.

## Before production

- **Hosting**: Codespaces sleeps when idle, so it is for demos only. For 24/7, deploy to Azure App Service / Container Apps or Render.
- **Token**: the API Setup token expires in about a day. Create a System User in Meta Business Settings for a permanent token.
- **Number**: register your own business number and complete business verification.
- **Queue**: replace FastAPI `BackgroundTasks` with a real queue (Azure Service Bus, Redis + RQ) so messages survive restarts.
- **Proactive alerts** (low stock, new order) outside the 24-hour window need approved template messages.
- **Media**: voice notes and photos are acknowledged but not processed yet (see TODO in `main.py`).
- **Cost**: service replies are billed per message from Oct 2026, so keep agent replies to one message where possible.
