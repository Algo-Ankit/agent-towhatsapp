# Agent to WhatsApp

**Vendors run their store by chatting on WhatsApp. AI agents do the work, 24/7.**

This repo is the WhatsApp interface layer of our agent-based e-commerce platform. It connects vendors on WhatsApp to our AI agents (Inventory Agent and Support Agent), so a vendor can type "add 20 rice bags" or "when is my payout?" in the app they already use every day, and the right agent executes it and replies within seconds.

---

## 1. The concept

### The problem
Small vendors (kirana stores, local sellers, D2C brands starting out) do not want to learn another dashboard. Updating stock, changing prices, chasing payouts and resolving issues happens late at night, on the go, from a phone. Every extra app or login is a reason not to keep the store updated, and stale inventory means lost orders.

### The idea
Meet vendors where they already are. Every vendor in India uses WhatsApp. So instead of making them log into our seller panel, we give them **one WhatsApp number** that is backed by AI agents:

- **Inventory Agent**: reads and updates stock, prices and products ("stock", "add 20 RICE5", "price RICE5 499", "what is running low?").
- **Support Agent**: answers questions about orders, payouts, policies and account issues, and escalates to a human when needed.

The vendor just chats. The agents act on our platform's data and reply on WhatsApp. No app install, no training, works on any phone.

### Why it matters (pitch points)
- **Zero onboarding friction**: if a vendor can send a WhatsApp message, they can run their store.
- **Always on**: agents respond at 2am the same as at 2pm; no support team needed for routine actions.
- **Safe by design**: any risky change (price change, setting stock to zero) needs the vendor to reply YES before it happens.
- **Agent-agnostic**: the WhatsApp layer is separate from the agents. We can improve, swap or add agents (orders, catalogue, marketing) without touching the WhatsApp side.

### What a vendor experiences
```
Vendor:  LINK SHARMA42
Agent:   Linked to Sharma Kirana Store. Send 'stock' to see your inventory.
Vendor:  stock
Agent:   ATTA10: Wheat Atta 10kg | qty 25 | Rs 410
         OIL1: Mustard Oil 1L | qty 8 | Rs 165
         RICE5: Basmati Rice 5kg | qty 40 | Rs 520
         Low stock: OIL1
Vendor:  add 10 OIL1
Agent:   Added 10 to OIL1. New qty: 18
Vendor:  price RICE5 499
Agent:   Change RICE5 price to Rs 499? Reply YES to confirm.
Vendor:  YES
Agent:   RICE5 price changed from Rs 520 to Rs 499
Vendor:  when is my payout
Agent:   Payouts are settled every Tuesday...
```

---

## 2. How it works

Important: we do **not** connect agents to each vendor's personal WhatsApp. We own **one official WhatsApp Business number**. Vendors message that number from their normal WhatsApp. We identify each vendor by their phone number.

```
 Vendor's WhatsApp
        |
        v
 Our WhatsApp Business number (Meta Cloud API)
        |  Meta POSTs every incoming message
        v
 +-------------------- this repo (WhatsApp bridge) --------------------+
 |  /webhook  ->  verify signature  ->  skip duplicates  ->  reply 200  |
 |                                |                                     |
 |                    background processing                            |
 |                                v                                     |
 |  router: who is this vendor? (phone -> vendor_id)                    |
 |          is this a YES/NO for a pending action?                      |
 |          which agent should handle it?                               |
 +-------------------------+--------------------------+----------------+
                           |                          |
                           v                          v
                   Inventory Agent              Support Agent
                (friend's agent, over HTTP or local Python)
                           |
                           v
              reply text  ->  Graph API  ->  Vendor's WhatsApp
```

### Key pieces
| Piece | What it does | File |
|---|---|---|
| Webhook | Receives messages from Meta, verifies signature, ignores retries, answers fast | `app/main.py` |
| WhatsApp client | Parses Meta's payload, sends replies | `app/whatsapp.py` |
| Vendor linking | Unknown numbers must send `LINK <code>` once; code comes from the vendor dashboard | `app/router.py`, `app/db.py` |
| Router | Picks Inventory or Support agent; handles YES/NO confirmations | `app/router.py` |
| Agent registry | Uses the real agent if its URL is set, otherwise a local stand-in | `app/agents/__init__.py` |
| Remote agent adapter | Calls an agent running as its own service | `app/agents/remote.py` |
| Stand-in agents | Simple working agents so the demo runs today | `app/agents/inventory.py`, `app/agents/support.py` |
| Agent server template | Starting point to wrap the real agents as HTTP endpoints | `examples/agent_server_template.py` |
| Simulator | Pretends to be a vendor; no Meta account needed | `scripts/simulate.py` |

### Safety rules built in
- **Vendor isolation**: every agent call carries `vendor_id`; agents must only touch that vendor's data.
- **Confirm before risky actions**: agents return a `pending` action; nothing happens until the vendor says YES (expires in 10 minutes).
- **Signature check**: messages without Meta's valid `X-Hub-Signature-256` are rejected in live mode.
- **Dedupe**: Meta retries webhooks; each message ID is processed once.
- **Agent failures never crash the bridge**: the vendor gets a polite "try again" message.

---

## 3. Team split

| Who | Owns |
|---|---|
| Agents (friend) | Inventory Agent and Support Agent logic, tools, data access |
| WhatsApp interface (this repo) | Webhook, vendor identity, routing, confirmations, sending replies, Meta setup |
| Contract between them | Section 5 below. As long as both sides follow it, either side can change freely |

---

## 4. Run it now (no Meta account needed)

### On your own machine (VS Code), in an isolated environment
Creates `.venv` inside the project so your global Python is untouched.
```bash
# Mac / Linux / Git Bash
bash scripts/setup.sh
source .venv/bin/activate
bash scripts/demo.sh
```
```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --port 8000          # terminal 1
python scripts\simulate.py                # terminal 2 (activate .venv there too)
```
In VS Code, pick the interpreter once: Ctrl+Shift+P > "Python: Select Interpreter" > the one under `.venv`. New terminals then activate it automatically.


### In GitHub Codespaces
Open this repo > **Code > Codespaces > Create codespace** (or open the existing one and run `git pull`). Dependencies and `.env` are set up automatically by `.devcontainer`. If you opened an older codespace, run:
```bash
pip install -r requirements.txt && cp -n .env.example .env
```

### Quickest: one command
```bash
bash scripts/demo.sh
```
Starts the bridge and opens a vendor chat in the same terminal; agent replies print right under your messages. Ctrl+C quits both.

### Or run server and chat separately
```bash
# terminal 1: the bridge
uvicorn app.main:app --port 8000

# terminal 2: pretend to be a vendor
python scripts/simulate.py "LINK SHARMA42" stock "add 10 OIL1" "price RICE5 499" YES "when is my payout"
# or interactive:
python scripts/simulate.py
```
Replies print in terminal 1. Check which agents are active at `http://localhost:8000/health`.

Demo commands: `LINK SHARMA42`, `stock`, `add 20 RICE5`, `set RICE5 qty 0`, `price RICE5 499`, `YES` / `NO`, anything about payouts or orders.

---

## 5. Plugging in the real agents

There are two options. **Option A is recommended** because it keeps the agents and the WhatsApp layer fully independent.

### Option A: agents run as a service (no code change here)
1. Your friend wraps each agent in an HTTP endpoint. `examples/agent_server_template.py` is a ready template with TODOs where their agent calls go.
2. Put the URLs in `.env`:
   ```
   INVENTORY_AGENT_URL=http://localhost:9001/inventory
   SUPPORT_AGENT_URL=http://localhost:9001/support
   AGENT_API_KEY=optional-shared-secret
   ```
3. Restart the bridge. `/health` will show `remote` for each agent.

Try it with the template:
```bash
uvicorn examples.agent_server_template:app --port 9001   # terminal 3
```

#### Agent API contract
The bridge sends a `POST` with JSON:
```json
{"type": "message", "vendor_id": "v_001", "vendor_name": "Sharma Kirana Store",
 "phone": "919812345678", "message": "price RICE5 499"}
```
The agent replies:
```json
{"reply": "Text the vendor will see on WhatsApp"}
```
For a risky action, the agent asks for confirmation instead of acting:
```json
{"reply": "Change RICE5 price to Rs 499? Reply YES",
 "pending": {"action": "set_price", "payload": {"sku": "RICE5", "price": 499}}}
```
If the vendor replies YES within 10 minutes, the bridge calls the **same agent** again:
```json
{"type": "confirm", "vendor_id": "v_001", "vendor_name": "...", "phone": "...",
 "action": "set_price", "payload": {"sku": "RICE5", "price": 499}}
```
and sends back whatever `reply` it returns. Timeout is 60 seconds.

### Option B: agents are Python code in this repo
Copy the agent code into `app/agents/` and replace the bodies of `handle()` and `confirm()` in `inventory.py` / `support.py`:
```python
def handle(vendor: dict, text: str) -> AgentResult: ...
def confirm(vendor: dict, action: str, payload: dict) -> str: ...
```

### Better routing (later)
`pick_agent()` in `app/router.py` uses keywords. Replace it with an LLM classifier, or point both URLs at one orchestrator agent that calls inventory and support as tools.

---

## 6. Connect real WhatsApp

**Shortcut:** after steps 1 to 3 below (Meta app, your phone in the "To" list, copy the IDs), run
```bash
bash scripts/go_live.sh
```
It asks for the Phone number ID, access token and app secret, checks them with Meta, writes `.env`, makes port 8000 public, starts the server, and prints the exact Callback URL and Verify token to paste in step 6. The manual steps are below.


1. **Meta app**: developers.facebook.com > Create app > Business type > add the **WhatsApp** product.
2. **API Setup** page: copy the temporary access token and **Phone number ID** into `.env`. Add your own phone under "To" as a test recipient (the free test number allows up to 5).
3. **App secret**: App settings > Basic > App secret, into `.env` as `WA_APP_SECRET`.
4. Set `DRY_RUN=0` in `.env` and restart the bridge.
5. **Public URL**:
   - Codespaces: **Ports** tab > port 8000 > right click > **Port Visibility > Public**. Copy the forwarded URL (looks like `https://<name>-8000.app.github.dev`).
   - Local: `ngrok http 8000`.
6. **Webhook**: WhatsApp > Configuration > Webhook > Edit. Callback URL `https://<public-url>/webhook`, Verify token = your `WA_VERIFY_TOKEN`. Verify and save, then **Subscribe** to the `messages` field.
7. From your phone, message the test number: `LINK SHARMA42`, then `stock`.

---

## 7. Before production

- **Hosting**: Codespaces sleeps when idle, so it is for demos only. For 24/7, deploy to Azure App Service / Container Apps or Render.
- **Token**: the API Setup token expires in about a day. Create a System User in Meta Business Settings for a permanent token.
- **Number**: register our own business number and complete Meta business verification.
- **Database**: move from SQLite to Postgres; vendors and link codes should come from the main platform.
- **Queue**: replace FastAPI `BackgroundTasks` with a real queue (Azure Service Bus, Redis) so messages survive restarts.
- **Proactive alerts** (low stock, new order) outside WhatsApp's 24-hour window need Meta-approved template messages.
- **Voice notes and photos**: common with Indian vendors. Currently acknowledged but not processed (see TODO in `app/main.py`); add speech-to-text and image handling next.
- **Policy**: WhatsApp bans general-purpose AI chatbots on the Business Platform (since Jan 2026). Our agents are task-specific (inventory and support), which is allowed; keep them scoped.
- **Cost**: from Oct 2026 Meta charges per service reply, so agents should answer in one message where possible and use buttons/lists to cut back-and-forth.

---

## 8. Roadmap
1. Swap stand-ins for the real Inventory and Support agents (Section 5).
2. Live demo on the Meta test number for investors.
3. Voice note support (Hindi + English) via speech-to-text.
4. Interactive buttons for confirmations and product lists.
5. Proactive alerts: low stock, new order, payout sent.
6. More agents: orders, catalogue onboarding from photos, marketing.
