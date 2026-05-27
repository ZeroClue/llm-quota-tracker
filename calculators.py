from providers.base import ProviderState


def calculate_budget(state: ProviderState, history: list[float]) -> ProviderState:
    if state.days_until_reset is None or state.remaining_quota is None or state.days_until_reset <= 0:
        return state
    flat = state.remaining_quota / state.days_until_reset
    if len(history) >= 2:
        recent = history[-7:]
        diffs = [recent[i] - recent[i + 1] for i in range(len(recent) - 1) if recent[i] > recent[i + 1]]
        if diffs:
            avg_daily_spend = sum(diffs) / len(diffs)
            state.current_pace = avg_daily_spend
            projected_runout = state.remaining_quota / avg_daily_spend
            if projected_runout < state.days_until_reset:
                state.daily_allowance = flat * 0.8
                state.status = "warning"
                return state
    state.daily_allowance = flat
    return state


def calculate_burst(state: ProviderState) -> ProviderState:
    if state.window_pct_used is not None:
        if state.window_pct_used > 80:
            state.status = "critical"
        elif state.window_pct_used > 60:
            state.status = "warning"
    return state
