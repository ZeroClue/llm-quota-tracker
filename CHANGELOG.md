# Changelog

## [0.3.0] - 2026-05-28

### Added
- `--help` flag with usage, options, and referral link
- `--json` flag for machine-readable provider data output
- `--setup` interactive configuration wizard with credential validation
- `setup_wizard.py` — per-provider instructions, input validation, retry logic

## [0.2.1] - 2026-05-27

### Fixed
- Sub-window percentage >80% now correctly sets provider status to critical (Zai weekly at 100% was showing as "ok")
- Health summary counts now reflect sub-window states

## [0.2.0] - 2026-05-27

### Changed
- Dashboard now split into Budget and Burst sections with column headers
- Progress bars using Unicode blocks, color-coded green/yellow/red
- Fixed-width padding for aligned bars across all providers
- Consistent window labels: 5h, 7d, M, MCP
- Centered health summary with count breakdown
- Spinner with status messages during data fetching
- Standardized column widths across tables
- README with attributions and referral link

### Fixed
- Claude OAuth token timezone parsing (was off by 2h)
- Ollama multi-line usage parsing (session + weekly)
- OpenCode Go SolidJS hydration regex for all three windows
- Config key aliasing for zai_glm → zai, ollama_cloud → ollama
- Factory lambda double-nesting bug (config was silently lost)
- Calculator history pace computation (day-over-day deltas, not raw averages)
- py-modules missing registry and discovery

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
