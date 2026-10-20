"""Adapter for agents that run as their own service (FastAPI, Azure AI Foundry endpoint, LangGraph, etc.).

Set INVENTORY_AGENT_URL / SUPPORT_AGENT_URL in .env and the bridge calls them over HTTP
instead of the local stand-ins. See README "Agent API contract" for the exact JSON.
"""
import httpx

from .base import AgentResult


class RemoteAgent:
    def __init__(self, name: str, url: str, api_key: str = ""):
        self.name = name
        self.url = url
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def _post(self, body: dict) -> dict:
        try:
            r = httpx.post(self.url, json=body, headers=self.headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # never crash the bridge because an agent is down
            print(f"[{self.name} agent error] {e}")
            return {"reply": "Sorry, that took too long. Please try again in a minute."}

    def handle(self, vendor: dict, text: str) -> AgentResult:
        data = self._post(
            {
                "type": "message",
                "vendor_id": vendor["id"],
                "vendor_name": vendor["name"],
                "phone": vendor["phone"],
                "message": text,
            }
        )
        pending = data.get("pending")
        return AgentResult(
            reply=data.get("reply", ""),
            pending=(pending["action"], pending.get("payload", {})) if pending else None,
        )

    def confirm(self, vendor: dict, action: str, payload: dict) -> str:
        data = self._post(
            {
                "type": "confirm",
                "vendor_id": vendor["id"],
                "vendor_name": vendor["name"],
                "phone": vendor["phone"],
                "action": action,
                "payload": payload,
            }
        )
        return data.get("reply", "Done.")
