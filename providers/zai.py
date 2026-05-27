import requests
import time
from providers.base import BaseProvider, ProviderState


ZAI_QUOTA_URL = "https://api.z.ai/api/monitor/usage/quota/limit"


class ZaiProvider(BaseProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Zai GLM", provider_type="burst", unit="tokens")
        if not self.api_key:
            state.status = "needs-auth"
            return state

        try:
            resp = requests.get(
                ZAI_QUOTA_URL,
                headers={
                    "Authorization": self.api_key,
                    "User-Agent": "OpenCode-Quota-Toast/1.0",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            limits = data.get("data", {}).get("limits", [])

            for limit in limits:
                pct = limit.get("percentage", 0)
                if limit.get("type") == "TOKENS_LIMIT" and limit.get("unit") == 3:
                    state.window_pct_used = pct
                    reset_ms = limit.get("nextResetTime")
                    if reset_ms:
                        secs = max(0, int(reset_ms / 1000 - time.time()))
                        state.window_resets_in = f"{secs // 3600}h {(secs % 3600) // 60}m"
                    return state
        except requests.RequestException:
            pass

        state.status = "critical"
        return state
