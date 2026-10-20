"""Stand-in support agent. Set SUPPORT_AGENT_URL in .env, or replace `handle`/`confirm` with your real agent."""
from .base import AgentResult


def handle(vendor: dict, text: str) -> AgentResult:
    t = text.lower()
    if "payout" in t or "payment" in t:
        return AgentResult(reply="Payouts are settled every Tuesday. Your next payout is being processed.")
    if "order" in t:
        return AgentResult(reply="You have 3 open orders. Reply 'order <id>' for details.")
    return AgentResult(
        reply="Support here. Ask me about payouts, orders, or account issues. Type 'human' to reach our team."
    )


def confirm(vendor: dict, action: str, payload: dict) -> str:
    return "Done."
