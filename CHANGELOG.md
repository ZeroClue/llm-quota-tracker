# Changelog

## [0.1.0] - 2026-05-27

### Added
- Initial project scaffold with `uv`, Python 3.11+
- `ProviderState` dataclass and `BaseProvider` ABC (`providers/base.py`)
- Budget and burst calculators (`calculators.py`)
- Config loader with YAML support (`config_loader.py`)
- SQLite history module for daily snapshots (`history.py`)
- Rich TUI dashboard with color-coded status (`ui.py`)
- Four providers:
  - Claude Code Pro — `claude auth status` + OAuth usage API
  - OpenCode Go — dashboard scrape with SolidJS hydration regex
  - Ollama Cloud Pro — web scrape `ollama.com/settings`
  - Zai GLM — REST API at `api.z.ai`
- Auto-discovery engine (`registry.py`, `discovery.py`)
- Multi-window display (5h, weekly, monthly, MCP per provider)
- Daily allowance and pace guidance
- OpenCode Go dollar conversion ($60/mo default budget)
- Multi-instance Claude support (`~/.claude*` directories)
- MIT License
