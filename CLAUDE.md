# CLAUDE.md

Context for Claude Code working in this repo.

## What this is
WhatsApp interface layer for an agent-based e-commerce startup. Vendors (small shops) message ONE WhatsApp Business number; Meta's Cloud API POSTs each message to our webhook; we identify the vendor by phone number, route to the Inventory Agent or Support Agent, and reply on WhatsApp. The two agents are built by a teammate and will be plugged in over HTTP; this repo owns everything WhatsApp-side.

## Architecture
- `app/main.py`: FastAPI. `GET /webhook` (Meta verify handshake), `POST /webhook` (inbound; verify signature, dedupe by message id, return 200 fast, process in background), `/` and `/health`.
- `app/whatsapp.py`: `X-Hub-Signature-256` check, payload parsing, `send_text` via Graph API. `DRY_RUN=1` prints replies instead of sending.
- `app/router.py`: unknown number -> only `LINK <code>` allowed; YES/NO handles pending confirmations; else `pick_agent` (keyword based) -> agent.
- `app/agents/__init__.py`: registry. If `INVENTORY_AGENT_URL` / `SUPPORT_AGENT_URL` set -> `RemoteAgent` (HTTP), else local stand-ins.
- Agent contract: `handle(vendor, text) -> AgentResult(reply, pending)` and `confirm(vendor, action, payload) -> str`. HTTP JSON contract is in README section 5 and `examples/agent_server_template.py`.
- `app/db.py`: SQLite (vendors, demo inventory, processed message ids, pending actions). Seeded vendor `v_001` "Sharma Kirana Store", link code `SHARMA42`.
- `scripts/simulate.py`: sends Meta-shaped payloads to the local webhook. `scripts/demo.sh`: server + chat in one terminal. `scripts/go_live.sh`: Codespaces go-live helper.

## Run
- Always use the project venv, never global Python: `bash scripts/setup.sh` (Mac/Linux) or `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1` (Windows), then activate `.venv`.
- Demo: `bash scripts/demo.sh`, or `uvicorn app.main:app --port 8000` + `python scripts/simulate.py`.
- Install new packages only inside `.venv` and add them to `requirements.txt`.

## Rules
- Never commit `.env` or print tokens/secrets.
- Every agent call must carry `vendor_id`; agents may only touch that vendor's data.
- Risky actions (price change, stock to zero, deletes) must go through the pending + YES confirmation flow.
- Webhook must return 200 quickly; slow work happens off the request path (Meta retries slow webhooks).
- Keep replies to one WhatsApp message where possible (Meta bills per service message).
- No em dashes in user-facing text or docs.
- After any change, run the simulator flow (`LINK SHARMA42`, `stock`, `price RICE5 499`, `YES`) to check nothing broke.

## Direction (planned)
- Event-based, scale-to-zero hosting (Azure Container Apps min replicas 0, or Azure Functions): webhook only verifies + enqueues; a queue-triggered worker runs the agent and replies.
- Move state from SQLite to a managed store (Postgres / Cosmos / Table Storage) since scale-to-zero has no persistent disk.
- Replace keyword `pick_agent` with an LLM classifier or one orchestrator agent.
- Voice notes (speech-to-text, Hindi + English), images, interactive buttons, template messages for proactive alerts.
