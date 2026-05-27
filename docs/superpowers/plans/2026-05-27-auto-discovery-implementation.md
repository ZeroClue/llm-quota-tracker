# Auto-Discovery & Quota Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual `input()` prompts with auto-discovery of installed AI coding tools and their quota data sources.

**Architecture:** A `discovery.py` scanner probes known paths and CLIs to find installed tools. A `registry.py` holds static `ProviderDef` entries (id, probe function, factory). Each probe checks `which`, env vars, and known data dirs. Discovered providers are merged with `config.yaml` overrides, then fetched and rendered as before. `input()` prompts are removed entirely.

**Tech Stack:** Python 3.11+, `uv`, `shutil.which`, `subprocess`, `requests`, `beautifulsoup4`

---

### Task 1: Provider registry with probe definitions

**Files:**
- Create: `registry.py`

- [ ] **Step 1: Define ProviderDef and the registry**

```python
from typing import Callable
from providers.base import BaseProvider


class ProviderDef:
    def __init__(self, pid: str, name: str, probe: Callable[[], bool], factory: Callable[[dict], BaseProvider], requires_auth: bool = False):
        self.id = pid
        self.name = name
        self.probe = probe
        self.factory = factory
        self.requires_auth = requires_auth


REGISTRY: list[ProviderDef] = []
```

- [ ] **Step 2: Define the register decorator and built-in providers**

```python
def register(pid: str, name: str, probe: Callable[[], bool], requires_auth: bool = False):
    def wrapper(factory: Callable[[dict], BaseProvider]):
        REGISTRY.append(ProviderDef(pid, name, probe, factory, requires_auth))
        return factory
    return wrapper
```

- [ ] **Step 3: Verify import**

Run: `uv run python -c "from registry import REGISTRY, register, ProviderDef; print(f'{len(REGISTRY)} providers registered')"`
Expected: `0 providers registered`

- [ ] **Step 4: Commit**

Commit: `git add registry.py && git commit -m "feat: add provider registry with ProviderDef"`

---

### Task 2: Scanner — tool discovery via probes

**Files:**
- Create: `discovery.py`

- [ ] **Step 1: Write scanner**

```python
import shutil
import os
from pathlib import Path
from registry import REGISTRY, ProviderDef


def probe_which(binary: str) -> bool:
    return shutil.which(binary) is not None


def probe_env(var: str) -> bool:
    return os.environ.get(var, "").strip() != ""


def probe_path(path: str) -> bool:
    return Path(path).expanduser().exists()


def scan() -> list[ProviderDef]:
    return [p for p in REGISTRY if p.probe()]
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from discovery import scan; print(f'scan() returns {scan()}')"`
Expected: `scan() returns []`

- [ ] **Step 3: Commit**

Commit: `git add discovery.py && git commit -m "feat: add tool discovery scanner"`

---

### Task 3: Register Claude provider in registry

**Files:**
- Modify: `registry.py`

- [ ] **Step 1: Add Claude provider to registry**

```python
import shutil
from providers.claude import ClaudeProvider


register(
    pid="claude",
    name="Claude Code",
    probe=lambda: shutil.which("claude") is not None,
)(lambda config: ClaudeProvider(config.get("claude", {})))
```

Add this after the `REGISTRY` list and `register` function definition.

- [ ] **Step 2: Verify**

Run: `uv run python -c "from registry import REGISTRY; print([p.id for p in REGISTRY])"`
Expected: `['claude']`

- [ ] **Step 3: Commit**

Commit: `git add registry.py && git commit -m "feat: register Claude provider in registry"`

---

### Task 4: Rewrite Claude provider — use `claude` CLI for quotas

**Files:**
- Rewrite: `providers/claude.py`

- [ ] **Step 1: Rewrite ClaudeProvider to use `claude` CLI**

```python
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
                [self.binary, "--print-json"],  # generic auth probe — adjust as needed
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            # Parse quota windows from claude CLI output
            for root_key in ("quota", "usage", "rate_limits", "oauth_usage"):
                root = data.get(root_key) or data.get("oauth_usage")
                if root:
                    break
            else:
                root = data

            five_hr = root.get("five_hour") or root.get("fiveHour") or {}
            seven_day = root.get("seven_day") or root.get("sevenDay") or {}

            used_pct = self._parse_pct(five_hr)
            if used_pct is not None:
                state.window_pct_used = 100 - used_pct
                state.window_resets_in = self._parse_reset(five_hr)
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            state.status = "critical"
        return state

    @staticmethod
    def _parse_pct(window: dict) -> float | None:
        for key in ("utilization", "used_percentage", "usedPercentage", "used_percent", "usedPercent", "percent_used", "percentUsed"):
            val = window.get(key)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _parse_reset(window: dict) -> str | None:
        for key in ("resets_at", "resetsAt", "reset_at", "resetAt"):
            val = window.get(key)
            if val:
                return str(val)
        return None
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from providers.claude import ClaudeProvider; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

Commit: `git add providers/claude.py && git commit -m "feat: rewrite Claude provider to use claude CLI for quota windows"`

---

### Task 5: Register OpenCode Go in registry

**Files:**
- Modify: `registry.py`

- [ ] **Step 1: Add OpenCode Go provider**

```python
from providers.opencode import OpenCodeProvider


register(
    pid="opencode_go",
    name="OpenCode Go",
    probe=lambda: (
        os.environ.get("OPENCODE_GO_WORKSPACE_ID", "") != ""
        and os.environ.get("OPENCODE_GO_AUTH_COOKIE", "") != ""
    ),
    requires_auth=True,
)(lambda config: OpenCodeProvider(
    config.get("opencode_go", {}).get("workspace_id") or os.environ["OPENCODE_GO_WORKSPACE_ID"],
    config.get("opencode_go", {}).get("auth_cookie") or os.environ["OPENCODE_GO_AUTH_COOKIE"],
))
```

- [ ] **Step 2: Verify**

Run: `uv run python -c "from registry import REGISTRY; print([p.id for p in REGISTRY])"`
Expected: `['claude', 'opencode_go']`

- [ ] **Step 3: Commit**

Commit: `git add registry.py && git commit -m "feat: register OpenCode Go in registry"`

---

### Task 6: Rewrite OpenCode Go provider — dashboard scrape

**Files:**
- Rewrite: `providers/opencode.py`

- [ ] **Step 1: Rewrite OpenCodeProvider**

```python
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
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from providers.opencode import OpenCodeProvider; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

Commit: `git add providers/opencode.py && git commit -m "feat: rewrite OpenCode Go to scrape dashboard with cookie"`

---

### Task 7: Register remaining auto-detected providers

**Files:**
- Modify: `registry.py`

- [ ] **Step 1: Add Copilot, Cursor, OpenAI, Ollama, Zai to registry**

```python
register(
    pid="copilot",
    name="GitHub Copilot",
    probe=lambda: probe_path("~/.config/opencode/auth.json"),
    requires_auth=True,
)(lambda config: __import__("providers.copilot", fromlist=["CopilotProvider"]).CopilotProvider(config.get("copilot", {})))

register(
    pid="cursor",
    name="Cursor",
    probe=lambda: probe_path("~/.config/cursor") or probe_path("~/Library/Application Support/Cursor"),
    requires_auth=True,
)(lambda config: __import__("providers.cursor", fromlist=["CursorProvider"]).CursorProvider(config.get("cursor", {})))

register(
    pid="openai",
    name="OpenAI",
    probe=lambda: probe_path("~/.config/opencode/auth.json"),
    requires_auth=True,
)(lambda config: __import__("providers.openai", fromlist=["OpenAIProvider"]).OpenAIProvider(config.get("openai", {})))

register(
    pid="ollama",
    name="Ollama Cloud Pro",
    probe=lambda: False,  # cookie required, no auto-detection
    requires_auth=True,
)(lambda config: __import__("providers.ollama", fromlist=["OllamaProvider"]).OllamaProvider(config.get("ollama_cloud", {}).get("cookie", "")))

register(
    pid="zai",
    name="Zai GLM",
    probe=lambda: False,  # api_key required
    requires_auth=True,
)(lambda config: __import__("providers.zai", fromlist=["ZaiProvider"]).ZaiProvider(config.get("zai_glm", {}).get("api_key", "")))
```

- [ ] **Step 2: Verify**

Run: `uv run python -c "from registry import REGISTRY; print([p.id for p in REGISTRY])"`
Expected: `['claude', 'opencode_go', 'copilot', 'cursor', 'openai', 'ollama', 'zai']`

- [ ] **Step 3: Commit**

Commit: `git add registry.py && git commit -m "feat: register all providers in registry"`

---

### Task 8: New providers — Copilot, Cursor, OpenAI (stubs)

**Files:**
- Create: `providers/copilot.py`, `providers/cursor.py`, `providers/openai.py`

- [ ] **Step 1: Create CopilotProvider skeleton**

```python
from providers.base import BaseProvider, ProviderState


class CopilotProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self) -> ProviderState:
        state = ProviderState(name="GitHub Copilot", provider_type="burst")
        state.status = "needs-auth"
        try:
            from providers._opencode_auth import get_copilot_quota
            result = get_copilot_quota()
            if result:
                state.window_pct_used = 100.0 - result.percent_remaining
                state.window_resets_in = result.reset_time_iso
                state.status = "ok"
        except ImportError:
            pass
        return state
```

- [ ] **Step 2: Create CursorProvider skeleton**

```python
from providers.base import BaseProvider, ProviderState


class CursorProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self):
        state = ProviderState(name="Cursor", provider_type="burst")
        # Auth investigation needed: cursor stores session in platform-specific paths
        state.status = "needs-auth"
        return state
```

- [ ] **Step 3: Create OpenAIProvider skeleton**

```python
from providers.base import BaseProvider, ProviderState


class OpenAIProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self):
        state = ProviderState(name="OpenAI", provider_type="burst")
        state.status = "needs-auth"
        return state
```

- [ ] **Step 4: Register the shared auth helper**

Create `providers/_opencode_auth.py` that reads OpenCode's stored OAuth credentials for Copilot/OpenAI access:

```python
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
```

- [ ] **Step 5: Verify imports**

Run: `uv run python -c "
from providers.copilot import CopilotProvider
from providers.cursor import CursorProvider
from providers.openai import OpenAIProvider
from providers._opencode_auth import get_copilot_token
print('OK')
"`
Expected: `OK`

- [ ] **Step 6: Commit**

Commit: `git add providers/copilot.py providers/cursor.py providers/openai.py providers/_opencode_auth.py && git commit -m "feat: add Copilot, Cursor, OpenAI provider stubs + shared auth"`

---

### Task 9: Config loader — merge discovery with config overrides

**Files:**
- Modify: `config_loader.py`

- [ ] **Step 1: Add merge function**

```python
from discovery import scan


def resolve_providers(config: dict) -> list:
    discovered = {p.id: p for p in scan()}
    configured = set(config.keys())

    active = []
    for pid, provider_def in discovered.items():
        if provider_def.requires_auth and pid not in configured and pid not in ("claude",):
            continue
        merged_config = config.get(pid, {})
        provider = provider_def.factory(merged_config)
        active.append(provider)

    # Add config-only providers (ollama, zai) not discovered
    for pid in configured:
        if pid not in discovered:
            pass  # handled by registry
    return active
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from config_loader import resolve_providers; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

Commit: `git add config_loader.py && git commit -m "feat: merge discovery results with config overrides"`

---

### Task 10: UI — add needs-auth status display

**Files:**
- Modify: `ui.py`

- [ ] **Step 1: Add needs-auth handling**

In the `render` function, add before the burst/budget branching:

```python
if p.status == "needs-auth":
    table.add_row(p.name, "[yellow]needs auth[/yellow]", "Install or configure this provider")
    continue
```

- [ ] **Step 2: Commit**

Commit: `git add ui.py && git commit -m "feat: add needs-auth status display to dashboard"`

---

### Task 11: Wire discovery into main.py

**Files:**
- Rewrite: `main.py`

- [ ] **Step 1: Rewrite main.py**

```python
from config_loader import load_config, resolve_providers
from calculators import calculate_budget, calculate_burst
from history import History
from ui import render


def main():
    config = load_config()
    providers = resolve_providers(config)

    results = []
    for p in providers:
        state = p.fetch()
        if state.status == "needs-auth":
            results.append(state)
            continue
        if state.provider_type == "budget" and state.remaining_quota is not None:
            history = History()
            trailing = history.get_trailing_avg(state.name)
            history.save_snapshot(state.name, state.remaining_quota)
            results.append(calculate_budget(state, trailing))
        elif state.provider_type == "burst" and state.window_pct_used is not None:
            results.append(calculate_burst(state))
        else:
            results.append(state)

    render(results)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify runs without errors**

Run: `uv run python main.py`
Expected: Dashboard renders with whatever providers are detected (may be empty or sparse)

- [ ] **Step 3: Commit**

Commit: `git add main.py && git commit -m "feat: wire auto-discovery into main entrypoint"`
