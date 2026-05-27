import re
import requests
from providers.base import BaseProvider, ProviderState


DASHBOARD_URL = "https://opencode.ai/workspace/{workspace_id}/go"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/148.0"


_RE_PCT_FIRST = re.compile(
    r"(rollingUsage|weeklyUsage|monthlyUsage):\$R\[\d+\]=\{(?:[^}])*?usagePercent:(-?\d+(?:\.\d+)?)(?:[^}])*?resetInSec:(-?\d+(?:\.\d+)?)(?:[^}])*?\}"
)
_RE_RESET_FIRST = re.compile(
    r"(rollingUsage|weeklyUsage|monthlyUsage):\$R\[\d+\]=\{(?:[^}])*?resetInSec:(-?\d+(?:\.\d+)?)(?:[^}])*?usagePercent:(-?\d+(?:\.\d+)?)(?:[^}])*?\}"
)


def _parse_windows(html: str) -> dict[str, dict]:
    windows = {}
    for match in re.finditer(_RE_PCT_FIRST, html):
        name, pct, reset = match.group(1), float(match.group(2)), float(match.group(3))
        windows[name] = {"usagePercent": pct, "resetInSec": reset}
    for match in re.finditer(_RE_RESET_FIRST, html):
        name, reset, pct = match.group(1), float(match.group(2)), float(match.group(3))
        if name not in windows:
            windows[name] = {"usagePercent": pct, "resetInSec": reset}
    return windows


class OpenCodeProvider(BaseProvider):
    def __init__(self, workspace_id: str = "", auth_cookie: str = "", api_key: str = ""):
        self.workspace_id = workspace_id
        self.auth_cookie = auth_cookie
        self.api_key = api_key

    def fetch(self) -> ProviderState:
        if not self.auth_cookie or not self.workspace_id:
            state = ProviderState(name="OpenCode Go", provider_type="budget")
            state.status = "needs-auth"
            return state

        try:
            resp = requests.get(
                DASHBOARD_URL.format(workspace_id=self.workspace_id),
                headers={
                    "User-Agent": USER_AGENT,
                    "Cookie": f"auth={self.auth_cookie}",
                },
                timeout=15,
            )
            resp.raise_for_status()
            windows = _parse_windows(resp.text)
            monthly = windows.get("monthlyUsage")
            if monthly:
                pct_used = monthly["usagePercent"]
                reset_sec = monthly["resetInSec"]
                state = ProviderState(name="OpenCode Go", provider_type="budget")
                state.remaining_quota = 100.0 - pct_used
                state.total_quota = 100.0
                state.days_until_reset = max(1, int(reset_sec / 86400))
                return state
        except requests.RequestException:
            pass

        state = ProviderState(name="OpenCode Go", provider_type="budget")
        state.status = "critical"
        return state
