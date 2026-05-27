from datetime import date, datetime
from providers.base import BaseProvider, ProviderState


MONTHLY_BUDGET = 60.0


class OpenCodeProvider(BaseProvider):
    def __init__(self, billing_cycle_start: str):
        self.billing_cycle_start = datetime.strptime(billing_cycle_start, "%Y-%m-%d").date()

    def fetch(self) -> ProviderState:
        today = date.today()
        days_until_reset = (self._next_billing_date() - today).days
        state = ProviderState(
            name="OpenCode Go",
            provider_type="budget",
            total_quota=MONTHLY_BUDGET,
            days_until_reset=days_until_reset,
        )
        try:
            remaining = float(input("Enter OpenCode remaining $ balance: "))
            state.remaining_quota = remaining
        except (ValueError, EOFError):
            state.status = "critical"
        return state

    def _next_billing_date(self) -> date:
        today = date.today()
        year, month = today.year, today.month
        if today.day >= self.billing_cycle_start.day:
            month += 1
        if month > 12:
            year += 1
            month = 1
        try:
            return date(year, month, self.billing_cycle_start.day)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, last_day)
