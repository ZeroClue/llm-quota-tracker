from pathlib import Path
import json


def _read_opencode_auth() -> dict | None:
    paths = [
        Path.home() / ".config" / "opencode" / "auth.json",
        Path.home() / ".local" / "share" / "opencode" / "auth.json",
    ]
    for p in paths:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    return None


def get_copilot_token() -> str | None:
    auth = _read_opencode_auth()
    if not auth:
        return None
    for key in ("copilot", "github", "github_copilot"):
        token = auth.get(key, {}).get("access_token") or auth.get(key, {}).get("token")
        if token:
            return token
    return None
