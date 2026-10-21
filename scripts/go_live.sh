#!/usr/bin/env bash
# Connect the bridge to real WhatsApp in one go (run inside GitHub Codespaces).
# You need 3 values from developers.facebook.com > your app > WhatsApp > API Setup:
#   Phone number ID, Temporary access token, and App secret (App settings > Basic).
cd "$(dirname "$0")/.." || exit 1

# Use the project's .venv if it exists (keeps your global Python clean)
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; elif [ -f .venv/Scripts/activate ]; then . .venv/Scripts/activate; fi
[ -f .env ] || cp .env.example .env

set_env() {  # set_env KEY VALUE  (replace or append in .env)
  if grep -q "^$1=" .env; then
    python3 - "$1" "$2" <<'PY'
import sys, re
k, v = sys.argv[1], sys.argv[2]
s = open(".env").read()
s = re.sub(rf"^{re.escape(k)}=.*$", lambda m: f"{k}={v}", s, flags=re.M)
open(".env", "w").write(s)
PY
  else
    echo "$1=$2" >> .env
  fi
}

echo "== WhatsApp go-live setup =="
echo "Paste each value from Meta's API Setup page (input is hidden for secrets)."
read -rp  "Phone number ID (long number, NOT the phone number): " PNID
read -rsp "Temporary access token (starts with EAA): " TOKEN; echo
read -rsp "App secret (App settings > Basic > Show): " SECRET; echo

PNID=$(echo "$PNID" | tr -d '[:space:]'); TOKEN=$(echo "$TOKEN" | tr -d '[:space:]'); SECRET=$(echo "$SECRET" | tr -d '[:space:]')
if [ -z "$PNID" ] || [ -z "$TOKEN" ] || [ -z "$SECRET" ]; then echo "All three values are required."; exit 1; fi
case "$PNID" in *[!0-9]*) echo "Phone number ID should be digits only. Check you copied the ID, not the number."; exit 1;; esac

VERIFY=$(grep -E "^WA_VERIFY_TOKEN=" .env | cut -d= -f2-)
if [ -z "$VERIFY" ] || [ "$VERIFY" = "change-me" ]; then VERIFY="store-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' \n')"; fi

set_env DRY_RUN 0
set_env WA_PHONE_NUMBER_ID "$PNID"
set_env WA_TOKEN "$TOKEN"
set_env WA_APP_SECRET "$SECRET"
set_env WA_VERIFY_TOKEN "$VERIFY"
echo "Saved to .env (never commit this file; it is in .gitignore)."

# Check the token and phone number ID against Meta before going further
echo "Checking credentials with Meta..."
CHECK=$(python3 - "$PNID" "$TOKEN" <<'PY'
import sys, httpx
pnid, tok = sys.argv[1], sys.argv[2]
try:
    r = httpx.get(f"https://graph.facebook.com/v23.0/{pnid}", params={"fields": "display_phone_number,verified_name"},
                  headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    d = r.json()
    if r.status_code == 200:
        print(f"OK|{d.get('display_phone_number','?')}|{d.get('verified_name','?')}")
    else:
        print("ERR|" + d.get("error", {}).get("message", r.text)[:200])
except Exception as e:
    print(f"ERR|{e}")
PY
)
if [[ "$CHECK" == OK* ]]; then
  IFS='|' read -r _ NUMBER NAME <<< "$CHECK"
  echo "Credentials work. Your agent's WhatsApp number: $NUMBER ($NAME)"
else
  echo "Meta rejected the credentials: ${CHECK#ERR|}"
  echo "Fix the value in Meta's API Setup page and run this script again."
  exit 1
fi

# Public URL (Codespaces) and port visibility
if [ -n "$CODESPACE_NAME" ]; then
  DOMAIN=${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}
  URL="https://${CODESPACE_NAME}-8000.${DOMAIN}"
  gh codespace ports visibility 8000:public -c "$CODESPACE_NAME" >/dev/null 2>&1 \
    && echo "Port 8000 set to Public." \
    || echo "Could not set port to Public automatically. Do it in the Ports tab: right click 8000 > Port Visibility > Public."
else
  URL="https://<your-public-url>"
  echo "Not in Codespaces: expose port 8000 with 'ngrok http 8000' and use that URL."
fi

pkill -f "uvicorn app.main:app" 2>/dev/null; sleep 1
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
sleep 3
gh codespace ports visibility 8000:public -c "$CODESPACE_NAME" >/dev/null 2>&1

cat <<MSG

============================================================
 Last step, in Meta (WhatsApp > Configuration > Webhook > Edit):

   Callback URL :  $URL/webhook
   Verify token :  $VERIFY

 Click "Verify and save", then under Webhook fields click
 Subscribe next to "messages".

 Then from YOUR phone (it must be in the API Setup "To" list),
 send WhatsApp messages to $NUMBER:
   LINK SHARMA42
   stock
============================================================
 Live log below (Ctrl+C stops watching; the server keeps running).
 To stop the server: pkill -f uvicorn
MSG
tail -f server.log
