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
