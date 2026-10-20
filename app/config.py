import os

from dotenv import load_dotenv

load_dotenv()

# From Meta App Dashboard > WhatsApp > API Setup
WA_TOKEN = os.getenv("WA_TOKEN", "")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "")
# Meta App Dashboard > App settings > Basic > App secret (used to verify webhook signatures)
WA_APP_SECRET = os.getenv("WA_APP_SECRET", "")
# Any string you choose; paste the same value in the Meta webhook config
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "change-me")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v23.0")

# DRY_RUN=1 prints replies to the console instead of calling Meta (for local testing)
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
DB_PATH = os.getenv("DB_PATH", "bridge.db")

# Your real agents. Leave empty to use the local stand-ins in app/agents/.
AGENT_URLS = {
    "inventory": os.getenv("INVENTORY_AGENT_URL", "").strip(),
    "support": os.getenv("SUPPORT_AGENT_URL", "").strip(),
}
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
