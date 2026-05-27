import requests
from bs4 import BeautifulSoup
from providers.base import BaseProvider, ProviderState


OLLAMA_URL = "https://ollama.com/settings"


class OllamaProvider(BaseProvider):
    def __init__(self, cookie: str):
        self.cookie = cookie

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Ollama Cloud Pro", provider_type="burst")
        try:
            resp = requests.get(
                OLLAMA_URL,
                headers={"Cookie": self.cookie},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            state.window_pct_used = self._extract_pct(text, "Session usage")
            state.window_resets_in = self._extract_reset(text)
        except requests.RequestException:
            print("Ollama scrape failed (cookie expired?). Enter manually:")
            try:
                state.window_pct_used = float(input(" Session usage %: "))
                state.window_resets_in = input(" Resets in: ")
            except (ValueError, EOFError):
                state.status = "critical"
        return state

    @staticmethod
    def _extract_pct(text: str, label: str) -> float | None:
        import re
        for line in text.splitlines():
            if label in line:
                m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                if m:
                    return float(m.group(1))
        return None

    @staticmethod
    def _extract_reset(text: str) -> str | None:
        import re
        for line in text.splitlines():
            if "reset" in line.lower():
                m = re.search(r"resets?\s+in\s+([\d\s+hdm]+)", line, re.I)
                if m:
                    return m.group(1).strip()
        return None
