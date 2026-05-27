from providers.base import BaseProvider, ProviderState


class ZaiProvider(BaseProvider):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Zai GLM", provider_type="budget", unit="tokens")
        if not self.api_key:
            state.status = "needs-auth"
            return state
        state.status = "critical"
        return state
