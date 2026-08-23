"""CLI entrypoint — terminal-first operator interface."""
from __future__ import annotations

import json
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from opensignal.core.config import settings
from opensignal.core.orchestrator import Orchestrator

app = typer.Typer(help="OpenSignal – Self-healing opportunity monitor")
console = Console()


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


@app.command()
def run(
    source: Optional[str] = typer.Argument(None, help="Source name; omit with --all"),
    all: bool = typer.Option(False, "--all", help="Run every enabled source"),
    force_heal: bool = typer.Option(False, help="Force heal even if quality passes"),
    simulate_drift: bool = typer.Option(
        False, "--simulate-drift", help="Simulate schema drift (e.g. missing organization)"
    ),
):
    """Run: scrape → quality gate → heal if needed → store."""
    _setup_logging()
    orch = Orchestrator(settings)

    if all or source is None:
        results = orch.run_all(force_heal=force_heal, simulate_drift=simulate_drift)
    else:
        results = [orch.run_one(source, force_heal=force_heal, simulate_drift=simulate_drift)]

    table = Table(title="OpenSignal Run Summary")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Quality")
    table.add_column("Records")
    table.add_column("Missing/Weak")

    for r in results:
        problems = []
        if r.get("missing"):
            problems.append("missing:" + ",".join(r["missing"]))
        if r.get("weak"):
            problems.append("weak:" + ",".join(r["weak"]))
        if r.get("error"):
            problems.append(r["error"])
        table.add_row(
            str(r.get("source", "?")),
            str(r.get("status", "?")),
            str(r.get("quality_score", r.get("quality_after", "-"))),
            str(r.get("records_fetched", r.get("saved", "-"))),
            " | ".join(problems) if problems else "",
        )
    console.print(table)
    console.print_json(data=results)


@app.command("list-sources")
def list_sources():
    """Show enabled playbooks."""
    orch = Orchestrator(settings)
    if not orch.playbooks:
        console.print(
            "[yellow]No enabled sources.[/yellow] "
            "Create collectors and set COLLECTOR_* in .env"
        )
        return
    for name, pb in orch.playbooks.items():
        console.print(
            f"[bold]{name}[/bold]  collector={pb.collector_id}  url={pb.base_url}"
        )


@app.command()
def status():
    """Show local config health (does not call Bright Data)."""
    console.print(f"DB path: {settings.open_signal_db_path}")
    console.print(f"Quality threshold: {settings.quality_threshold}")
    console.print(f"Auto-approve heal: {settings.auto_approve_heal}")
    orch = Orchestrator(settings)
    console.print(f"Enabled sources: {list(orch.playbooks.keys()) or '(none)'}")


if __name__ == "__main__":
    app()
