from rich.console import Console
from rich.table import Table
from rich import box
from providers.base import ProviderState


def render(providers: list[ProviderState]):
    console = Console()
    table = Table(title="LLM Daily Allowance Tracker", box=box.ROUNDED)
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Details")

    for p in providers:
        status_style = {"ok": "green", "warning": "yellow", "critical": "red"}.get(p.status, "white")
        sep = "" if p.unit in ("$", "%") else " "
        if p.provider_type == "budget":
            if p.remaining_quota is not None and p.total_quota is not None and p.days_until_reset is not None:
                details = f"{p.unit}{sep}{p.remaining_quota:.2f} / {p.unit}{sep}{p.total_quota:.0f} remaining ({p.days_until_reset}d left)"
                if p.daily_allowance is not None:
                    details += f"\nAllowance: {p.unit}{sep}{p.daily_allowance:.2f}/day"
                if p.current_pace is not None:
                    details += f"\nPace: {p.unit}{sep}{p.current_pace:.2f}/day"
            else:
                details = "No data"
        else:
            if p.window_pct_used is not None:
                details = f"Window: {p.window_pct_used:.0f}% used"
            else:
                details = "Window: N/A"
            if p.window_resets_in:
                details += f"\nResets: {p.window_resets_in}"

        table.add_row(p.name, f"[{status_style}]{p.status}[/{status_style}]", details)

    console.print(table)
