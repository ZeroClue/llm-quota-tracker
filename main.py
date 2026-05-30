import sys
import json as json_module
from rich.console import Console
from config_loader import load_config, resolve_providers
from calculators import calculate_budget, calculate_burst
from history import History
from ui import render


def main():
    if "--help" in sys.argv:
        print("Usage: llm-tracker [--help] [--json] [--setup]")
        print()
        print("Auto-discovers AI coding tools and displays quota usage.")
        print()
        print("Options:")
        print("  --help     Show this message and exit")
        print("  --json     Output provider data as JSON (machine-readable)")
        print("  --setup    Interactive configuration wizard")
        print()
        print("Supported providers: Claude Code, OpenCode Go, Ollama Cloud Pro, Zai GLM")
        print("Config: ~/.config/llm-tracker/config.yaml")
        print()
        print("Built with OpenCode — https://opencode.ai/go?ref=JAFCG08A7T")
        return

    if "--setup" in sys.argv:
        if "--json" in sys.argv:
            print("Error: --json and --setup are mutually exclusive")
            sys.exit(1)
        from setup_wizard import run_setup
        run_setup()
        return

    console = Console()
    config = load_config()
    providers = resolve_providers(config)

    results = []
    with console.status("") as status:
        for p in providers:
            name = type(p).__name__.replace("Provider", "")
            status.update(f"[cyan]{name}[/cyan] — fetching usage...")
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
            status.update(f"[green]✓[/green] {state.name}")

    if "--json" in sys.argv:
        data = []
        for r in results:
            d = {"name": r.name, "status": r.status, "provider_type": r.provider_type}
            if r.provider_type == "budget":
                d["remaining"] = r.remaining_quota
                d["total"] = r.total_quota
                d["days_left"] = r.days_until_reset
                d["daily_allowance"] = r.daily_allowance
                d["pace"] = r.current_pace
                d["unit"] = r.unit
            if r.window_pct_used is not None:
                d["used_pct"] = r.window_pct_used
                d["window_label"] = r.window_label
                d["resets_in"] = r.window_resets_in
            d["windows"] = [{"label": w.label, "used_pct": w.pct_used, "resets_in": w.resets_in} for w in r.windows]
            if r.status == "needs-auth":
                d["message"] = "Not configured"
            d = {k: v for k, v in d.items() if v is not None}
            data.append(d)
        print(json_module.dumps(data, indent=2))
    else:
        render(results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Interrupted.")
        sys.exit(1)
