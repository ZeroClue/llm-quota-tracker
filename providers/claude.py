import subprocess
import json
import os
from pathlib import Path
from providers.base import BaseProvider, ProviderState


ANTHROPIC_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"


def _scan_claude_instances() -> list[dict]:
    home = Path.home()
    instances = []
    for p in sorted(home.glob(".claude*")):
        if not p.is_dir():
            continue
        creds_file = p / ".credentials.json"
        config_file = p / ".claude.json"
        label = p.name.removeprefix(".claude") or "default"
        instance = {"path": p, "label": label, "creds_file": creds_file, "config_file": config_file}
        try:
            env = {**os.environ, "CLAUDE_CONFIG_DIR": str(p)}
            result = subprocess.run(
                ["claude", "auth", "status"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            data = json.loads(result.stdout)
            instance["logged_in"] = data.get("loggedIn", False)
            instance["subscription"] = data.get("subscriptionType", "unknown")
            instance["auth_method"] = data.get("authMethod", "")
            instance["email"] = data.get("email", "")
            instance["probe_worked"] = True
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            instance["logged_in"] = False
            instance["subscription"] = "unknown"
            instance["probe_worked"] = True
        instances.append(instance)
    return instances


class ClaudeProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self) -> ProviderState:
        instances = _scan_claude_instances()
        if not instances:
            state = ProviderState(name="Claude Code", provider_type="burst")
            state.status = "critical"
            return state

        for inst in instances:
            if not inst["logged_in"]:
                continue

            label = inst["label"]
            name = f"Claude Code ({label})" if label != "default" else "Claude Code"
            sub = inst.get("subscription", "unknown")

            state = ProviderState(name=name, provider_type="burst")
            creds_path = inst["creds_file"]
            if creds_path.exists():
                usage = _query_usage_api(creds_path)
                if usage:
                    root = usage.get("quota") or usage.get("usage") or usage.get("oauth_usage") or usage
                    five_hr = root.get("five_hour") or root.get("fiveHour") or {}
                    used_pct = _parse_pct(five_hr)
                    if used_pct is not None:
                        state.window_pct_used = 100.0 - used_pct
                        state.window_resets_in = _parse_reset(five_hr)
                        return state

            state.status = "ok"
            state.window_resets_in = f"plan: {sub}"
            return state

        state = ProviderState(name="Claude Code", provider_type="burst")
        state.status = "critical"
        return state


def _query_usage_api(creds_path: Path) -> dict | None:
    import requests
    try:
        data = json.loads(creds_path.read_text())
        oauth = data.get("claudeAiOauth") or data.get("oauth") or {}
        token = oauth.get("accessToken") or oauth.get("access_token") or oauth.get("token")
        if not token:
            return None
        resp = requests.get(
            ANTHROPIC_USAGE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Anthropic-Beta": "oauth-2025-04-20",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except (FileNotFoundError, json.JSONDecodeError, requests.RequestException):
        pass
    return None


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
