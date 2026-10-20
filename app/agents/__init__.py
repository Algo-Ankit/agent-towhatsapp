"""Agent registry. Each agent exposes:
    handle(vendor: dict, text: str) -> AgentResult
    confirm(vendor: dict, action: str, payload: dict) -> str

If <NAME>_AGENT_URL is set, the remote service is used; otherwise the local stand-in.
"""
from .. import config
from . import inventory as _local_inventory
from . import support as _local_support
from .remote import RemoteAgent


def _build():
    agents = {}
    for name, local in (("inventory", _local_inventory), ("support", _local_support)):
        url = config.AGENT_URLS.get(name)
        agents[name] = RemoteAgent(name, url, config.AGENT_API_KEY) if url else local
    return agents


AGENTS = _build()


def describe():
    return {n: ("remote " + a.url if isinstance(a, RemoteAgent) else "local stand-in") for n, a in AGENTS.items()}
