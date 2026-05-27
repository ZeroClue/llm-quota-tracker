import re
import requests
from bs4 import BeautifulSoup
from providers.base import BaseProvider, ProviderState, QuotaWindow


OLLAMA_URL = "https://ollama.com/settings"


def _extract_windows(text: str) -> list[dict]:
    lines = text.splitlines()
    windows = []
    current = None

    for line in lines:
        if "Session usage" in line:
            current = {"label": "Session", "pct": None, "reset": None}
        elif "Weekly usage" in line:
            current = {"label": "Weekly", "pct": None, "reset": None}
        elif current is not None:
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
            if m and current["pct"] is None:
                current["pct"] = float(m.group(1))
            m = re.search(r"resets?\s+in\s+([\d\s+hdm]+)", line, re.I)
            if m and current["reset"] is None:
                current["reset"] = m.group(1).strip()
            if current["pct"] is not None and current["reset"] is not None:
                windows.append(current)
                current = None

    if current is not None and current["pct"] is not None:
        windows.append(current)

    return windows


class OllamaProvider(BaseProvider):
    def __init__(self, cookie: str):
        self.cookie = cookie

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Ollama Cloud Pro", provider_type="burst")
        if not self.cookie:
            state.status = "needs-auth"
            return state
        try:
            resp = requests.get(
                OLLAMA_URL,
                headers={"Cookie": self.cookie},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            windows = _extract_windows(text)

            for w in windows:
                if w["label"] == "Session":
                    state.window_pct_used = w["pct"]
                    state.window_resets_in = w["reset"]
                elif w["label"] == "Weekly":
                    state.windows.append(QuotaWindow(
                        label="Weekly", pct_used=w["pct"], resets_in=w["reset"],
                    ))

            if state.window_pct_used is None:
                state.status = "needs-auth"
        except requests.RequestException:
            state.status = "needs-auth"
        return state
