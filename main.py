from rich.console import Console
from config_loader import load_config, resolve_providers
from calculators import calculate_budget, calculate_burst
from history import History
from ui import render


def main():
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

    render(results)


if __name__ == "__main__":
    main()
