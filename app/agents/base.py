from dataclasses import dataclass


@dataclass
class AgentResult:
    reply: str
    # (action_name, payload_dict) when the agent wants the vendor to reply YES before acting
    pending: tuple[str, dict] | None = None
