import requests
import time
from providers.base import BaseProvider, ProviderState, QuotaWindow


ZAI_QUOTA_URL = "https://api.z.ai/api/monitor/usage/quota/limit"

WINDOW_LABELS = {(3, "TOKENS_LIMIT"): "5h", (6, "TOKENS_LIMIT"): "Weekly", (5, "TIME_LIMIT"): "MCP"}


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
                limit_type = limit.get("type")
                unit = limit.get("unit")
                pct = limit.get("percentage", 0)
                label = WINDOW_LABELS.get((unit, limit_type))
                if not label:
                    continue

                reset_ms = limit.get("nextResetTime")
                resets_in = None
                if reset_ms:
                    secs = max(0, int(reset_ms / 1000 - time.time()))
                    if secs >= 86400:
                        resets_in = f"{secs // 86400}d"
                    elif secs >= 3600:
                        resets_in = f"{secs // 3600}h {(secs % 3600) // 60}m"
                    else:
                        resets_in = f"{secs // 60}m"

                if label == "5h":
                    state.window_pct_used = pct
                    state.window_label = "5h"
                    state.window_resets_in = resets_in
                else:
                    state.windows.append(QuotaWindow(label=label, pct_used=pct, resets_in=resets_in))

            if state.window_pct_used is not None:
                return state
        except requests.RequestException:
            pass

        state.status = "critical"
        return state
