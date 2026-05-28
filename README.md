# LLM Quota Tracker

A terminal dashboard that auto-discovers your AI coding tools and shows all your quotas, daily allowances, and usage windows in one place.

Supports Claude Code Pro, OpenCode Go, Ollama Cloud Pro, Zai GLM, and extensible to more.

[Powered by OpenCode](https://opencode.ai/go?ref=JAFCG08A7T)

## Features

- **Auto-discovery** — detects installed tools via `which`, known paths, and credential files
- **Unified dashboard** — color-coded tables with progress bars, sectioned by budget/burst
- **Multi-window display** — each provider shows all its quota windows (5h, 7d, monthly, MCP)
- **Daily allowance** — remaining ÷ days until reset tells you your safe daily spend
- **Pace tracking** — SQLite history tracks day-over-day usage, warns on overspend
- **No manual prompts** — missing credentials show "needs auth" gracefully
- **No cloud dependencies** — all state lives in `~/.config/llm-tracker/`

## Try OpenCode

This tool was built with and runs on [OpenCode](https://opencode.ai/go?ref=JAFCG08A7T), the open-source AI coding agent.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

### Quick install (recommended)

```bash
uv tool install git+https://github.com/ZeroClue/llm-quota-tracker.git
```

Then run from anywhere:

```bash
llm-tracker
```

### Or clone and run

```bash
git clone https://github.com/ZeroClue/llm-quota-tracker.git
cd llm-quota-tracker
uv sync
uv run llm-tracker
```

### Upgrade

```bash
uv tool upgrade llm-quota-tracker
```

## Usage

```bash
uv run llm-tracker
```

![Dashboard preview](docs/images/capture.png)

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

| Provider | Windows | Plan detection |
|----------|---------|---------------|
| Claude Code | 5h + 7d | Pro via OAuth |
| OpenCode Go | 5h + 7d + Monthly | $60/mo budget (configurable) |
| Ollama Cloud Pro | 5h + 7d | Cloud Pro |
| Zai GLM | 5h + 7d + MCP | Pro via API |

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

## Attributions

This project builds on ideas from several excellent open-source tools:

- **[opencode-quota](https://github.com/slkiser/opencode-quota)** by slkiser — SolidJS hydration regex scraping, provider pattern, Anthropic OAuth usage API approach
- **[tokscale](https://github.com/junhoyeo/tokscale)** by junhoyeo — Tool discovery and scanning concept, multi-platform data sources
- **[ccusage](https://github.com/ryoppippi/ccusage)** by ryoppippi — Claude Code data sources and CLI integration
- **[OpenCode](https://opencode.ai/go?ref=JAFCG08A7T)** — The open-source AI coding agent this project is built with and for

## Development

```bash
uv add <package>   # add a dependency
uv run python      # run scripts
```

No test or lint infrastructure yet.

## License

MIT
