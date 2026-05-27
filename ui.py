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
        if p.status == "needs-auth":
            table.add_row(p.name, "[yellow]needs auth[/yellow]", "Install or configure this provider")
            continue
        status_style = {"ok": "green", "warning": "yellow", "critical": "red"}.get(p.status, "white")
        sep = "" if p.unit in ("$", "%") else " "
        if p.provider_type == "budget":
            if p.remaining_quota is not None and p.total_quota is not None and p.days_until_reset is not None:
                details = f"{p.unit}{sep}{p.remaining_quota:.2f} / {p.unit}{sep}{p.total_quota:.0f} remaining ({p.days_until_reset}d left)"
                if p.daily_allowance is not None:
                    details += f"\nAllowance: {p.unit}{sep}{p.daily_allowance:.2f}/day"
                    if p.status == "warning" and p.current_pace is not None:
                        details += f"\n⚠️ Pace {p.unit}{sep}{p.current_pace:.2f}/day — slow to {p.unit}{sep}{p.daily_allowance:.2f}/day"
                    elif p.current_pace is not None:
                        details += f"\n✅ Pace {p.unit}{sep}{p.current_pace:.2f}/day — on track"
                    else:
                        details += f"\n✅ {p.unit}{sep}{p.daily_allowance:.2f}/day keeps you through the month"
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

        for w in p.windows:
            w_details = f"{w.label}: {w.pct_used:.0f}% used" if w.pct_used is not None else f"{w.label}: N/A"
            if w.pct_used is not None and w.pct_used >= 100:
                w_details += " 🔴 limit reached"
            elif w.pct_used is not None and w.pct_used >= 80:
                w_details += " ⚠️ almost full"
            if w.resets_in:
                w_details += f" · resets {w.resets_in}"
            table.add_row("", "", w_details)

    console.print(table)
