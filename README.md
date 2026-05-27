# LLM Quota Tracker

A terminal dashboard that auto-discovers your AI coding tools and shows all your quotas, daily allowances, and usage windows in one place.

Supports Claude Code Pro, OpenCode Go, Ollama Cloud Pro, Zai GLM, and extensible to more.

## Features

- **Auto-discovery** — detects installed tools via `which`, known paths, and credential files
- **Unified dashboard** — single `rich` table showing all providers with color-coded status
- **Multi-window display** — each provider shows all its quota windows (5h, weekly, monthly, MCP)
- **Daily allowance** — remaining ÷ days until reset tells you your safe daily spend
- **Pace tracking** — SQLite history tracks day-over-day usage, warns on overspend
- **No manual prompts** — missing credentials show "needs auth" gracefully
- **No cloud dependencies** — all state lives in `~/.config/llm-tracker/`

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone https://github.com/ZeroClue/llm-quota-tracker.git
cd llm-quota-tracker
uv sync
```

## Usage

```bash
uv run llm-tracker
```

Providers are auto-detected. Claude and OpenCode Go appear automatically if installed. Configure credentials for others in `~/.config/llm-tracker/config.yaml`:

```yaml
# OpenCode Go — get workspace_id and auth_cookie from browser DevTools
opencode_go:
  workspace_id: "wrk_xxxxxxxx"
  auth_cookie: "Fe26.2****"

# Ollama Cloud Pro — paste full Cookie header from browser Network tab
ollama_cloud:
  cookie: "__Secure_session=...; aid=..."

# Zai GLM — API key from account settings
zai_glm:
  api_key: "your_key"
```

### Auto-discovered providers

| Provider | What's detected | Data source |
|----------|---------------|-------------|
| Claude Code | `~/.claude*` directories | `claude auth status` + OAuth usage API |
| OpenCode Go | `which opencode` | Dashboard scrape with workspace_id + auth cookie |
| Ollama Cloud Pro | Config only | Web scrape `ollama.com/settings` with cookie |
| Zai GLM | Config only | API at `api.z.ai/api/monitor/usage/quota/limit` |

## Supported Providers

All providers show their quota windows when configured:

| Provider | Windows | Plan |
|----------|---------|------|
| Claude Code | 5h + 7d | Pro detected via OAuth |
| OpenCode Go | 5h + Weekly + Monthly | $60/mo budget (configurable) |
| Ollama Cloud Pro | Session + Weekly | Cloud Pro |
| Zai GLM | 5h + Weekly + MCP | Pro via API |

## Architecture

```
registry.py         — Static provider definitions with probe functions
discovery.py        — Scanner probes which, paths, env vars
config_loader.py    — Merges discovery results with config.yaml overrides
providers/base.py   — ProviderState dataclass + BaseProvider ABC + QuotaWindow
providers/claude.py — Claude Code (OAuth usage API)
providers/opencode.py — OpenCode Go (SolidJS hydration regex scrape)
providers/ollama.py — Ollama Cloud Pro (BeautifulSoup scrape)
providers/zai.py    — Zai GLM (REST API)
calculators.py      — calculate_budget() + calculate_burst()
history.py          — SQLite daily snapshots for pace
ui.py               — Rich table with color-coded status + guidance
```

Status colors: green (on track), yellow (over pace), red (critical / limit reached).

## Development

```bash
uv add <package>   # add a dependency
uv run python      # run scripts
```

No test or lint infrastructure yet.

## License

MIT
