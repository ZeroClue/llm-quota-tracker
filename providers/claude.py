import subprocess
import json
from providers.base import BaseProvider, ProviderState


class ClaudeProvider(BaseProvider):
    def __init__(self, config: dict):
        self.binary = config.get("binary_path", "claude")

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Claude Code", provider_type="burst")
        try:
            result = subprocess.run(
                [self.binary, "--print-json"],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            root = data.get("quota") or data.get("usage") or data.get("rate_limits") or data.get("oauth_usage") or data

            five_hr = root.get("five_hour") or root.get("fiveHour") or {}
            used_pct = _parse_pct(five_hr)
            if used_pct is not None:
                state.window_pct_used = 100.0 - used_pct
                state.window_resets_in = _parse_reset(five_hr)
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            state.status = "critical"
        return state


def _parse_pct(window: dict) -> float | None:
    for key in ("utilization", "used_percentage", "usedPercentage", "used_percent", "usedPercent", "percent_used", "percentUsed"):
        val = window.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return None


def _parse_reset(window: dict) -> str | None:
    for key in ("resets_at", "resetsAt", "reset_at", "resetAt"):
        val = window.get(key)
        if val:
            return str(val)
    return None
