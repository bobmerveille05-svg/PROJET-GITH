"""Ceremony level management commands."""

from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from spectra.ceremony.assessor import CeremonyAssessor
from spectra.ceremony.enforcer import CeremonyEnforcer
from spectra.ceremony.levels import get_level_description
from spectra.ceremony.models import CeremonyLevel
from spectra.core.config import load_config
from spectra.core.database import get_connection
from spectra.intent_graph.query_engine import IntentGraphEngine
from spectra.intent_graph.store import SpecStore

app = typer.Typer()
console = Console()


@app.command("check")
def check_ceremony(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Run ceremony checks for a spec."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Find spec
        spec = store.get_spec(spec_ref)
        if not spec:
            spec = store.get_spec_by_name(spec_ref)

        if not spec:
            console.print(f"[red]Error:[/red] Spec not found: {spec_ref}")
            raise typer.Exit(1)

        # Get spec data
        yaml_content = store.get_spec_yaml(spec.id)
        spec_data = yaml.safe_load(yaml_content)

        # Run checks for current level
        current_level = CeremonyLevel(spec.ceremony_level)
        enforcer = CeremonyEnforcer()
        results = enforcer.enforce_ceremony(spec_data, current_level)

        console.print(f"\n[bold]Ceremony Check:[/bold] {spec.name}")
        console.print(f"Current Level: [cyan]{current_level.name}[/cyan] ({current_level.value})")
        console.print(f"Description: {get_level_description(current_level)}\n")

        # Display results
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)

        for result in results:
            status_icon = "[green]✓[/green]" if result.passed else "[red]✗[/red]"
            console.print(f"{status_icon} {result.check_name}: {result.details}")

        console.print(f"\n[bold]Progress:[/bold] {passed_count}/{total_count} checks passed")

        if passed_count == total_count:
            console.print("[green]All ceremony requirements met![/green]")
        else:
            console.print(f"[yellow]{total_count - passed_count} checks remaining[/yellow]")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("suggest")
def suggest_level(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Suggest appropriate ceremony level for a spec."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Find spec
        spec = store.get_spec(spec_ref)
        if not spec:
            spec = store.get_spec_by_name(spec_ref)

        if not spec:
            console.print(f"[red]Error:[/red] Spec not found: {spec_ref}")
            raise typer.Exit(1)

        # Get spec data and graph context
        yaml_content = store.get_spec_yaml(spec.id)
        spec_data = yaml.safe_load(yaml_content)

        # Build graph context
        specs = store.list_specs()
        edges = store.get_all_edges()
        engine = IntentGraphEngine()
        engine.build_graph(specs, edges)

        dependents = engine.get_dependents(spec.id)
        graph_context = {"dependents": dependents}

        # Assess
        assessor = CeremonyAssessor()
        details = assessor.get_assessment_details(spec_data, graph_context)

        console.print(f"\n[bold]Ceremony Assessment:[/bold] {spec.name}\n")
        console.print(f"Change Category: [cyan]{details['category'].upper()}[/cyan]")
        console.print(f"Suggested Level: [cyan]{details['suggested_level'].name}[/cyan] ({details['suggested_level'].value})")
        console.print(f"Description: {get_level_description(details['suggested_level'])}\n")

        console.print("[bold]Assessment Factors:[/bold]")
        factors = details['factors']
        console.print(f"  Files: {factors['files_count']}")
        console.print(f"  Modules: {factors['modules_count']}")
        console.print(f"  Dependencies: {factors['dependencies_count']}")
        console.print(f"  Dependents: {factors['dependents_count']}")
        console.print(f"  Risks: {factors['risks_count']}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("report")
def ceremony_report() -> None:
    """Show project-wide ceremony status."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        specs = store.list_specs()

        if not specs:
            console.print("No specs found.")
            conn.close()
            return

        # Count by level
        level_counts: dict[int, int] = {}
        for spec in specs:
            level_counts[spec.ceremony_level] = level_counts.get(spec.ceremony_level, 0) + 1

        console.print("\n[bold]Project Ceremony Report[/bold]\n")

        table = Table(show_header=True)
        table.add_column("Level")
        table.add_column("Name")
        table.add_column("Count", justify="center")

        for level_val in range(6):
            level = CeremonyLevel(level_val)
            count = level_counts.get(level_val, 0)
            table.add_row(str(level_val), level.name, str(count))

        console.print(table)
        console.print(f"\n[bold]Total Specs:[/bold] {len(specs)}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
