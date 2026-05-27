import subprocess
import json
from providers.base import BaseProvider, ProviderState


class ClaudeProvider(BaseProvider):
    def fetch(self) -> ProviderState:
        state = ProviderState(name="Claude Code Pro", provider_type="burst")
        try:
            result = subprocess.run(
                ["ccusage", "claude", "daily", "--json"],
                capture_output=True, text=True, timeout=15
            )
            data = json.loads(result.stdout)
            state.window_pct_used = data.get("usage_pct")
            state.window_resets_in = data.get("resets_in")
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            print("ccusage not available. Enter usage % manually:")
            try:
                pct = float(input(" 5hr window usage %: "))
                state.window_pct_used = pct
                reset = input(" Resets in (e.g. '2h 15m'): ")
                state.window_resets_in = reset
            except (ValueError, EOFError):
                state.status = "critical"
        return state
