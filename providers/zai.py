from providers.base import BaseProvider, ProviderState


class ZaiProvider(BaseProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch(self) -> ProviderState:
        state = ProviderState(
            name="Zai GLM",
            provider_type="budget",
            unit="tokens",
        )
        try:
            remaining = float(input("Enter Zai GLM remaining tokens: "))
            total = float(input("Enter Zai GLM total token limit: "))
            days = int(input("Days until 30-day window resets: "))
            state.remaining_quota = remaining
            state.total_quota = total
            state.days_until_reset = days
            burst_pct = float(input(" 5hr burst usage % (0 if unknown): "))
            if burst_pct:
                state.window_pct_used = burst_pct
        except (ValueError, EOFError):
            state.status = "critical"
        return state
