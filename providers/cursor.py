from providers.base import BaseProvider, ProviderState


class CursorProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self) -> ProviderState:
        state = ProviderState(name="Cursor", provider_type="burst")
        state.status = "needs-auth"
        return state
