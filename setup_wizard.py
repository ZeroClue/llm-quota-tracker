import sys
import yaml
from pathlib import Path
import requests
from config_loader import CONFIG_DIR, LOCAL_CONFIG_PATH

CONFIG_PATH = CONFIG_DIR / "config.yaml"


def _prompt(label: str, secret: bool = False) -> str:
    val = input(f"{label}: ").strip()
    return val


def _validate_ollama(cookie: str) -> bool:
    try:
        resp = requests.get("https://ollama.com/settings", headers={"Cookie": cookie}, timeout=15)
        return "Session usage" in resp.text
    except requests.RequestException:
        return False


def _validate_opencode(workspace_id: str, auth_cookie: str) -> bool:
    try:
        from providers.opencode import _parse_windows
        resp = requests.get(
            f"https://opencode.ai/workspace/{workspace_id}/go",
            headers={"Cookie": f"auth={auth_cookie}", "User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        return "monthlyUsage" in resp.text
    except requests.RequestException:
        return False


def _validate_zai(api_key: str) -> bool:
    try:
        resp = requests.get(
            "https://api.z.ai/api/monitor/usage/quota/limit",
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=15,
        )
        return resp.status_code == 200 and resp.json().get("success") is True
    except (requests.RequestException, ValueError):
        return False


def _setup_provider(name: str, instructions: list[str], fields: list[dict], validate_fn) -> dict | None:
    print(f"\n--- {name} ---")
    for line in instructions:
        print(f"  {line}")

    for attempt in range(3):
        values = {}
        for f in fields:
            values[f["key"]] = _prompt(f["label"], secret=f.get("secret", False))

        print("  Validating...", end=" ")
        if validate_fn(**values):
            print("✅ Valid!")
            return values
        else:
            print("❌ Could not verify.")
            if attempt < 2:
                retry = input("  Retry? (y/n): ").strip().lower()
                if retry != "y":
                    return None
            else:
                print("  Skipped after 3 attempts.")
                return None
    return None


def run_setup():
    # Read existing config
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
    elif LOCAL_CONFIG_PATH.exists():
        with open(LOCAL_CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}

    has_oc = "opencode_go" in config
    has_ollama = "ollama_cloud" in config
    has_zai = "zai_glm" in config
    has_claude = True  # auto-detected

    print()
    print("╭────────────────────────────────────────╮")
    print("│     LLM Quota Tracker — Setup          │")
    print("├────────────────────────────────────────┤")
    print(f"│ ✓ Claude Code              auto-detect │")
    print(f"│ {'✓' if has_oc else ' '} OpenCode Go              {'configured' if has_oc else 'needs config'} │")
    print(f"│ {'✓' if has_ollama else ' '} Ollama Cloud Pro        {'configured' if has_ollama else 'needs config'} │")
    print(f"│ {'✓' if has_zai else ' '} Zai GLM                 {'configured' if has_zai else 'needs config'} │")
    print("╰────────────────────────────────────────╯")
    print()

    providers_to_setup = []

    if not has_oc:
        result = _setup_provider(
            "OpenCode Go",
            [
                "1. Log into https://opencode.ai in your browser",
                "2. Navigate to the Go page — URL should be:",
                "   https://opencode.ai/workspace/wrk_xxx/go",
                "3. The workspace ID is the wrk_xxx part of the URL",
                "4. Open DevTools → Storage → Cookies → opencode.ai",
                "5. Copy the value of the 'auth' cookie (starts with Fe26.2**)",
            ],
            [
                {"key": "workspace_id", "label": "  Workspace ID"},
                {"key": "auth_cookie", "label": "  Auth cookie", "secret": True},
            ],
            _validate_opencode,
        )
        if result:
            config["opencode_go"] = result

    if not has_ollama:
        result = _setup_provider(
            "Ollama Cloud Pro",
            [
                "1. Log into https://ollama.com in your browser",
                "2. Open DevTools → Network tab",
                "3. Refresh the page, click any request to ollama.com",
                "4. Find Request Headers → Cookie, copy the entire value",
            ],
            [
                {"key": "cookie", "label": "  Cookie header", "secret": True},
            ],
            _validate_ollama,
        )
        if result:
            config["ollama_cloud"] = result

    if not has_zai:
        result = _setup_provider(
            "Zai GLM",
            [
                "1. Log into your Z.ai account",
                "2. Navigate to API Keys in your settings",
                "3. Copy your API key",
            ],
            [
                {"key": "api_key", "label": "  API key", "secret": True},
            ],
            _validate_zai,
        )
        if result:
            config["zai_glm"] = {"api_key": result["api_key"]}

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    print()
    print("╭────────────────────────────────────────╮")
    print("│     Setup Complete                     │")
    print("├────────────────────────────────────────┤")
    print(f"│ ✓ Claude Code              auto-detect │")
    print(f"│ {'✓' if has_oc or 'opencode_go' in config else ' '} OpenCode Go              {'configured' if 'opencode_go' in config else 'skipped'} │")
    print(f"│ {'✓' if has_ollama or 'ollama_cloud' in config else ' '} Ollama Cloud Pro        {'configured' if 'ollama_cloud' in config else 'skipped'} │")
    print(f"│ {'✓' if has_zai or 'zai_glm' in config else ' '} Zai GLM                 {'configured' if 'zai_glm' in config else 'skipped'} │")
    print("╰────────────────────────────────────────╯")
    print()
    print("Run 'llm-tracker' to see your quota dashboard!")
    print()
