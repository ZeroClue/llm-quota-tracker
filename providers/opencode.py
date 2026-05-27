import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from providers.base import BaseProvider, ProviderState


OPENCODE_GO_URL = "https://opencode.ai/workspace/{workspace_id}/go"


def _read_opencode_go_auth() -> dict | None:
    paths = [
        Path.home() / ".local" / "share" / "opencode" / "auth.json",
        Path.home() / ".config" / "opencode" / "auth.json",
    ]
    for p in paths:
        if p.exists():
            try:
                data = json.loads(p.read_text())
                entry = data.get("opencode-go") or data.get("opencode_go") or {}
                if entry.get("type") == "api" and entry.get("key"):
                    return entry
            except (json.JSONDecodeError, KeyError):
                pass
    return None


class OpenCodeProvider(BaseProvider):
    def __init__(self, workspace_id: str = "", auth_cookie: str = "", api_key: str = ""):
        self.workspace_id = workspace_id
        self.auth_cookie = auth_cookie
        self.api_key = api_key

    def fetch(self) -> ProviderState:
        state = ProviderState(name="OpenCode Go", provider_type="budget")
        if self.auth_cookie and self.workspace_id:
            try:
                resp = requests.get(
                    OPENCODE_GO_URL.format(workspace_id=self.workspace_id),
                    headers={"Cookie": f"auth={self.auth_cookie}"},
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text()
                import re
                monthly_match = re.search(r'monthly.*?(\d+(?:\.\d+)?)\s*%', text, re.I)
                if monthly_match:
                    pct_used = float(monthly_match.group(1))
                    state.remaining_quota = 100.0 - pct_used
                    state.total_quota = 100.0
                    return state
            except requests.RequestException:
                pass

        state.status = "needs-auth"
        return state
