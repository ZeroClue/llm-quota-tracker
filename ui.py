from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich import box
from providers.base import ProviderState


def render(providers: list[ProviderState]):
    console = Console()

    counts = {"ok": 0, "warning": 0, "critical": 0, "needs-auth": 0}
    for p in providers:
        s = p.status if p.status in counts else "needs-auth"
        counts[s] += 1

    parts = []
    if counts["ok"]:
        parts.append(f"[green]🟢 {counts['ok']} healthy[/green]")
    if counts["warning"]:
        parts.append(f"[yellow]🟡 {counts['warning']} warnings[/yellow]")
    if counts["critical"]:
        parts.append(f"[red]🔴 {counts['critical']} limit reached[/red]")
    if counts["needs-auth"]:
        parts.append(f"[white]⚪ {counts['needs-auth']} needs auth[/white]")
    if parts:
        console.print("  ".join(parts))
        console.print()

    def bar_text(pct: float | None, width: int = 12) -> Text:
        if pct is None:
            return Text("")
        filled = int(width * min(pct / 100.0, 1.0))
        color = "green" if pct < 60 else ("yellow" if pct < 80 else "red")
        return Text("█" * filled + "░" * (width - filled), style=color)

    for section_type, section_label in [("budget", "Budget"), ("burst", "Burst")]:
        section = [p for p in providers if p.provider_type == section_type]
        if not section:
            continue

        table = Table(title=section_label, box=box.ROUNDED, show_header=False)
        table.add_column("Provider", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold", width=10)
        table.add_column("Details")

        for p in section:
            if p.status == "needs-auth":
                table.add_row(p.name, "[yellow]needs auth[/yellow]", "Install or configure this provider")
                continue

            status_style = {"ok": "green", "warning": "yellow", "critical": "red"}.get(p.status, "white")
            sep = "" if p.unit in ("$", "%") else " "

            if section_type == "budget":
                if p.remaining_quota is not None and p.total_quota is not None and p.days_until_reset is not None:
                    details = f"{p.unit}{sep}{p.remaining_quota:.2f} / {p.unit}{sep}{p.total_quota:.0f} ({p.days_until_reset}d)"
                    if p.daily_allowance is not None:
                        details += f"\nAllowance: {p.unit}{sep}{p.daily_allowance:.2f}/day"
                        if p.current_pace is not None:
                            details += f"  Pace: {p.unit}{sep}{p.current_pace:.2f}/day"
                        elif p.status == "ok":
                            details += "  ✅"
                else:
                    details = "No data"
            else:
                t = Text("")
                if p.window_pct_used is not None:
                    label = p.window_label or "Window"
                    t.append(f"{label} ")
                    t.append(bar_text(p.window_pct_used))
                    t.append(f" {p.window_pct_used:.0f}% used")
                else:
                    t = Text("Window: N/A")
                if p.window_resets_in:
                    t.append(f" resets {p.window_resets_in}")

            table.add_row(p.name, f"[{status_style}]{p.status}[/{status_style}]", details if section_type == "budget" else t)

            for w in p.windows:
                wt = Text("")
                if w.pct_used is not None:
                    wt.append(f"{w.label} ")
                    wt.append(bar_text(w.pct_used))
                    wt.append(f" {w.pct_used:.0f}% used")
                    if w.pct_used >= 100:
                        wt.append(" 🔴 max", style="red")
                else:
                    wt = Text(f"{w.label}: N/A")
                if w.resets_in:
                    wt.append(f"  resets {w.resets_in}")
                table.add_row("", "", wt)

        console.print(table)
        console.print()
