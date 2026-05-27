import requests
from bs4 import BeautifulSoup
from providers.base import BaseProvider, ProviderState


OPENCODE_GO_URL = "https://opencode.ai/workspace/{workspace_id}/go"


class OpenCodeProvider(BaseProvider):
    def __init__(self, workspace_id: str, auth_cookie: str):
        self.workspace_id = workspace_id
        self.auth_cookie = auth_cookie

    def fetch(self) -> ProviderState:
        state = ProviderState(name="OpenCode Go", provider_type="budget")
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
        except requests.RequestException:
            state.status = "critical"
        return state
