# Auto-Discovery & Quota Engine — Design Spec

**Goal:** Auto-detect all AI coding tools on the user's machine, figure out authentication, and present a unified quota dashboard without manual configuration or input prompts.

**Principle:** Borrow from existing open-source solutions (tokscale's scanner, opencode-quota's provider system, ccusage's data sources) rather than reverse‑engineering each tool from scratch.

---

## 1. Architecture

```
Scanner → Provider Registry → [Provider.fetch() → ProviderState] → Calculator → Dashboard
```

### Discovery phase (new: `discovery.py`)
Probe known paths and CLIs to find which tools the user has:

- `which <binary>` — check for `claude`, `opencode`, `ccusage`, `opencode-quota`
- Known data dirs — `~/.local/share/opencode/`, `~/.claude/`, `~/.config/opencode/`
- Environment variables — `OPENCODE_GO_WORKSPACE_ID`, `OPENCODE_GO_AUTH_COOKIE`
- OAuth sessions — OpenCode's stored credentials for Copilot and OpenAI

Each probe returns a confidence score: "definitely installed" vs. "probably installed" vs. "not found".

### Config merge (modify: `config_loader.py`)
Discovery results merge with optional `config.yaml` overrides:

```yaml
# config.yaml overrides for providers that need it
ollama_cloud:
  cookie: "..."  # required: no auto-detection possible

zai_glm:
  api_key: "..."  # optional: skip if not set, no prompt

# Provider-specific overrides (optional)
opencode_go:
  workspace_id: "wrk_..."
  auth_cookie: "Fe26.2..."

claude:
  binary_path: "/custom/path/claude"
```

Providers found by discovery run automatically. Providers in config but not discovered are skipped silently.

---

## 2. Provider Data Sources

### Claude Code (`providers/claude.py` — rewrite)

**Auth:** Auto-detected via `which claude`. OAuth token in `~/.claude/.credentials.json`.

**Data source:** Run `claude` CLI to get auth status + quota windows as JSON. The CLI returns two windows:
- `five_hour.percentRemaining` — 5-hour rolling window
- `seven_day.percentRemaining` — 7-day rolling window
- `resetTimeIso` for each window

**Fallback:** Read `~/.claude/.credentials.json` → extract OAuth `accessToken` → call `POST https://api.anthropic.com/api/oauth/usage`.

**Supplemental:** If `ccusage` is installed, use it for historical token data (pace calculation). Otherwise, the history module tracks remaining quota day-over-day, which implicitly tracks pace.

**Removed:** Manual `input()` prompts for usage percentage.

### OpenCode Go (`providers/opencode.py` — rewrite)

**Auth:** `OPENCODE_GO_WORKSPACE_ID` + `OPENCODE_GO_AUTH_COOKIE` env vars or config. Discovered by probing `which opencode` and checking env.

**Data source:** Scrape `https://opencode.ai/workspace/{workspace_id}/go` with auth cookie. Extract rolling, weekly, and monthly quota windows.

**Removed:** Manual `$` input prompt.

### GitHub Copilot (`providers/copilot.py` — new)

**Auth:** Reuses OpenCode's OAuth session (stored by `opencode auth login`). Auto-detected when OpenCode credentials exist.

**Data source:** `GET /copilot_internal/user` (Copilot's internal API) → premium request quota: used/total/remaining + reset time.

### Cursor (`providers/cursor.py` — new)

**Auth:** Session cookie from Cursor IDE installation. Discovered via known config paths.

**Data source:** Cursor usage API → premium request quota.

### OpenAI (`providers/openai.py` — new)

**Auth:** Reuses OpenCode's OAuth session. Auto-detected when OpenCode credentials exist.

**Data source:** `POST https://chatgpt.com/backend-api/wham/usage` → rate-limit windows (5h, 7d, etc.) derived from the API's reported durations.

### Ollama Cloud Pro (`providers/ollama.py` — keep current)

**Auth:** Cookie from config.yaml (no auto-detection possible).

**Data source:** Web scrape `ollama.com/settings` (unchanged).

### Zai GLM (`providers/zai.py` — keep current structure)

**Auth:** API key from config.yaml.

**Data source:** API call with api_key. Falls back to manual input only if explicitly requested.

---

## 3. Provider Interface

No change to `BaseProvider`:

```python
class BaseProvider(ABC):
    @abstractmethod
    def fetch(self) -> ProviderState: ...
```

New helper: `registry.py` manages the list of known providers and their discovery criteria:

```python
class ProviderDef:
    id: str
    probe: Callable[[], bool]  # returns True if provider is available
    factory: Callable[[], BaseProvider]
    requires_auth: bool
```

The registry is a static list of 7+ known providers, each with its probe function. The scanner iterates the registry, runs probes, and collects all available providers.

---

## 4. Changes to Existing Files

| File | Change |
|------|--------|
| `discovery.py` | NEW — scanner probes paths, `which`, env vars |
| `registry.py` | NEW — static provider definitions with probe functions |
| `providers/claude.py` | REWRITE — use `claude` CLI JSON instead of `ccusage` |
| `providers/opencode.py` | REWRITE — dashboard scrape instead of manual input |
| `providers/copilot.py` | NEW — Copilot internal API |
| `providers/cursor.py` | NEW — Cursor usage API |
| `providers/openai.py` | NEW — OpenAI usage API |
| `providers/ollama.py` | KEEP — web scrape (unchanged) |
| `providers/zai.py` | KEEP — API/manual (structure unchanged) |
| `config_loader.py` | MODIFY — merge discovery results with config overrides |
| `main.py` | MODIFY — add discovery phase before provider fetch |
| `ui.py` | MODIFY — show "detected, needs auth" status, remove "No data" |

---

## 5. Removed Behavior

- No forced `input()` prompts for usage data (manual input discouraged but available via `--manual` flag)
- No more silent skipping — detected providers always appear, even if unauth'd
- Undetected providers don't appear at all
- No more `status="critical"` from EOF errors on stdin
- No more hardcoded 4-provider limit — the registry can grow

## 7. Status States

Each provider has three possible states in the dashboard:

| State | Meaning | Example |
|-------|---------|---------|
| `"ok"` / `"warning"` / `"critical"` | Quota data fetched, normal budget/burst status | "Claude Code — 5hr: 67% remaining" |
| `"needs-auth"` | Tool detected but no credentials found | "Copilot — needs login (run `opencode auth login`)" |
| Not shown | Tool not detected at all | — |

---

## 6. Out of Scope (v1 of this change)

- Tokscale's full 24-tool set (start with 7)
- Writing our own OAuth flows (reuse existing credentials)
- The `--setup` command (deferred to packaging phase)
- Windows-specific path handling (probe supports it, not tested)
