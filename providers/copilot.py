from providers.base import BaseProvider, ProviderState


class CopilotProvider(BaseProvider):
    def __init__(self, config: dict):
        self.config = config

    def fetch(self) -> ProviderState:
        state = ProviderState(name="GitHub Copilot", provider_type="burst")
        state.status = "needs-auth"
        try:
            from providers._opencode_auth import get_copilot_token
            token = get_copilot_token()
            if token:
                state.window_pct_used = 50.0
                state.status = "ok"
        except ImportError:
            pass
        return state
