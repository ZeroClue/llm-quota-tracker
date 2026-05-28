import re
import requests
from providers.base import BaseProvider, ProviderState, QuotaWindow


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


def _fmt_reset(secs: float) -> str:
    if secs < 3600:
        return f"{int(secs // 60)}m"
    elif secs < 86400:
        return f"{int(secs // 3600)}h {int((secs % 3600) // 60)}m"
    else:
        return f"{int(secs // 86400)}d"


class OpenCodeProvider(BaseProvider):
    def __init__(self, workspace_id: str = "", auth_cookie: str = "", api_key: str = "",
                 monthly_budget: float = 60.0, weekly_budget: float = 30.0, rolling_budget: float = 12.0):
        self.workspace_id = workspace_id
        self.auth_cookie = auth_cookie
        self.api_key = api_key
        self.budgets = {"monthlyUsage": monthly_budget, "weeklyUsage": weekly_budget, "rollingUsage": rolling_budget}

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
            raw = _parse_windows(resp.text)
            monthly = raw.get("monthlyUsage")
            if monthly:
                pct_used = monthly["usagePercent"]
                reset_sec = monthly["resetInSec"]
                monthly_budget = self.budgets["monthlyUsage"]
                remaining_dollars = monthly_budget * (100.0 - pct_used) / 100.0
                state = ProviderState(name="OpenCode Go", provider_type="budget", unit="$")
                state.remaining_quota = remaining_dollars
                state.total_quota = monthly_budget
                state.days_until_reset = max(1, int(reset_sec / 86400))

                state.windows.append(QuotaWindow(
                    label="M",
                    pct_used=pct_used,
                    resets_in=_fmt_reset(reset_sec),
                ))

                for key, label in [("rollingUsage", "5h"), ("weeklyUsage", "7d")]:
                    w = raw.get(key)
                    if w:
                        budget = self.budgets.get(key, 0)
                        used = budget * w["usagePercent"] / 100.0
                        remaining = budget - used
                        state.windows.append(QuotaWindow(
                            label=label,
                            pct_used=w["usagePercent"],
                            resets_in=_fmt_reset(w["resetInSec"]),
                        ))
                return state
        except requests.RequestException:
            pass

        state = ProviderState(name="OpenCode Go", provider_type="budget")
        state.status = "critical"
        return state
