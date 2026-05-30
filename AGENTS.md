# LLM Quota Tracker — Agent Guide

## Stack & setup

- **Python 3.11+** with **`uv`** package manager
- Dependencies: `rich`, `requests`, `beautifulsoup4`, `pyyaml`
- Add deps: `uv add <package>`
- Run: `uv run llm-tracker` or `uv run python main.py`
- No lint/test/typecheck infra exists yet — do not assume any

## Current state (auto-discovery added)

- **Core engine**: `providers/base.py` (`ProviderState` dataclass, `BaseProvider` ABC), `calculators.py` (budget/burst math), `config_loader.py` (YAML config + discovery merge)
- **7 providers**: `claude.py` (`claude` CLI for quota windows), `opencode.py` (dashboard scrape), `copilot.py` (stub), `cursor.py` (stub), `openai.py` (stub), `ollama.py` (web scrape), `zai.py` (API/manual)
- **Auto-discovery**: `registry.py` (7 `ProviderDef` entries with probe functions), `discovery.py` (probes `which`, paths, env vars)
- **No manual input prompts** — providers are auto-detected or show "needs auth" status
- **History**: `history.py` — SQLite daily snapshots in `~/.config/llm-tracker/history.db`
- **TUI**: `ui.py` — rich table with color-coded status + "needs auth" for undetected providers
- **Shared auth**: `providers/_opencode_auth.py` — reads OpenCode's OAuth credentials for Copilot/OpenAI
- **Entrypoint**: `uv run llm-tracker` or `uv run python main.py`. `--help`, `--json`, `--setup` flags available.
- **Setup wizard**: `--setup` walks through credential collection with validation (Ollama cookie, OpenCode workspace_id + auth, Zai API key).
- **No lint/test/typecheck infra yet**

## Architecture

- **Discovery phase**: `registry.py` defines known providers with probe functions (which, path, env). `discovery.py::scan()` iterates REGISTRY, returns active ones.
- **Config merge**: `config_loader.py::resolve_providers()` merges discovered providers with `config.yaml` overrides.
- **Provider pattern**: Each LLM is a `BaseProvider` subclass. No more `input()` prompts — providers return "needs-auth" status when credentials are missing.
- **Two quota models**: `"budget"` (monthly cap) and `"burst"` (rolling window)
- **Data math**: `calculators.py` — daily allowance = remaining / days_until_reset; pace computed from day-over-day deltas
- **State**: SQLite `history.db` in `~/.config/llm-tracker/` for daily snapshots (pace calculation)
- **Config**: `config.yaml` (gitignored, user-local) holds optional credentials/cookies for providers that need them
- **Data sources**: Claude via `claude auth status` with `CLAUDE_CONFIG_DIR`, OpenCode Go via SolidJS hydration regex scrape, Ollama via `ollama.com/settings` scrape, Zai via `api.z.ai/api/monitor/usage/quota/limit` API, Copilot/Cursor/OpenAI via credential-based API (stubs)
- **Claude multi-instance**: Scans `~/.claude*` directories, runs `claude auth status` with `CLAUDE_CONFIG_DIR` to detect logged-in instances. Falls back to OAuth usage API when credentials have a valid `accessToken`.
- **Guiding principle**: Auto-detect first, config overrides second, no manual prompts
## OpenCode config

- `.opencode/opencode.json` configures MCP cache proxy
- `.agents/skills/` has 18 available skills (TDD, brainstorming, code review, litellm, etc.) — load as needed

## Future ideas (resurface later)

- **Copilot/Cursor/OpenAI real API integrations**: The stubs need the actual API endpoints and credential formats filled in. The shared auth helper (`_opencode_auth.py`) reads OpenCode's auth.json but the exact keys and endpoints need verification against opencode-quota's source.
