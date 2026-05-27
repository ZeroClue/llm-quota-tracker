# LLM Quota Tracker

A terminal dashboard that monitors multiple LLM subscriptions in one place. See how much quota you have left, your daily allowance, and whether you're spending too fast — across Claude Code Pro, OpenCode Go, Ollama Cloud Pro, and Zai GLM.

## Features

- **Unified dashboard** — single `rich` table showing all providers at once
- **Two quota models** — "budget" (monthly cap) and "burst" (rolling window)
- **Daily allowance math** — remaining ÷ days until reset tells you your safe daily spend
- **Pace tracking** — trailing 7-day average from SQLite history warns if you're overspending
- **Three-tier data fetching** — API/CLI → web scrape → manual input, falls back gracefully
- **No cloud dependencies** — all state lives in `~/.config/llm-tracker/`

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone <repo-url>
cd llm-quota-tracker
uv sync
```

## Configuration

Create `~/.config/llm-tracker/config.yaml` or a local `config.yaml`:

```yaml
opencode_go:
  billing_cycle_start: "2026-05-01"

ollama_cloud:
  cookie: "your_ollama_session_cookie"

claude_code:
  use_ccusage: true

zai_glm:
  api_key: ""
```

All fields are optional — providers without config still prompt for manual input.

## Usage

```bash
uv run llm-tracker
```

Providers appear in the dashboard automatically. If a data source is unavailable, you'll be prompted for input.

## Supported Providers

| Provider | Model | Data Source | Unit |
|----------|-------|-------------|------|
| Claude Code Pro | Burst (5hr window) | `ccusage` CLI or manual | % |
| OpenCode Go | Budget ($60/mo) | Manual input | $ |
| Ollama Cloud Pro | Burst (session/weekly) | Web scrape `ollama.com/settings` or manual | % |
| Zai GLM | Hybrid (30-day + 5hr burst) | Manual input | tokens |

## Architecture

```
main.py             — Entry point: wires config → providers → history → calculator → UI
config_loader.py    — Reads config.yaml from ~/.config/llm-tracker/ or local dir
providers/base.py   — ProviderState dataclass + BaseProvider ABC
providers/claude.py — Claude Code Pro (burst, ccsage CLI)
providers/opencode.py — OpenCode Go (budget, manual input)
providers/ollama.py — Ollama Cloud Pro (burst, web scrape)
providers/zai.py    — Zai GLM (hybrid, manual input)
calculators.py      — Pure functions: calculate_budget(), calculate_burst()
history.py          — SQLite daily snapshots for pace calculation
ui.py               — Rich table dashboard with color-coded status
```

Status colors: green (on track), yellow (warning), red (critical / over limit).

## Guiding Principles

- **Directionally correct** — a good estimate beats no data
- **Data first, UI second** — get numbers into ProviderState, format later
- **Fallback gracefully** — API → scrape → manual input, never leave the user with nothing
- **Local-only** — credentials in `config.yaml`, history in SQLite, nothing in the cloud

## Development

```bash
uv add <package>   # add a dependency
uv run python      # run scripts
```

No test or lint infrastructure yet.
