"""Spec management commands."""

import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from spectra.core.config import load_config
from spectra.core.database import get_connection
from spectra.core.events import EventBus
from spectra.intent_graph.models import Edge, EdgeType, IntentNode
from spectra.intent_graph.parser import parse_spec_file
from spectra.intent_graph.query_engine import IntentGraphEngine
from spectra.intent_graph.store import SpecStore
from spectra.intent_graph.visualizer import to_ascii_tree, to_rich_table, to_rich_tree
from spectra.lifecycle import history as lifecycle_history

app = typer.Typer()
console = Console()


@app.command("new")
def new_spec(
    name: str = typer.Argument(..., help="Spec name"),
) -> None:
    """Create a new spec from template."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Generate ID
        spec_id = name.lower().replace(" ", "-").replace("_", "-")

        # Check if spec already exists
        if store.get_spec(spec_id) or store.get_spec_by_name(name):
            console.print(f"[red]Error:[/red] Spec already exists: {name}")
            raise typer.Exit(1)

        # Load template
        template_path = Path(__file__).parent.parent.parent / "templates" / "specs" / "default.yaml"
        with open(template_path, "r") as f:
            template_content = f.read()

        # Replace placeholders
        spec_content = template_content.replace("{{ spec_id }}", spec_id)
        spec_content = spec_content.replace("{{ spec_name }}", name)

        # Parse to node
        node = IntentNode(
            id=spec_id,
            name=name,
            intent="TODO: Define the intent for this spec",
        )

        # Create spec
        store.create_spec(node, spec_content)

        console.print(f"[green]✓[/green] Created spec: [cyan]{name}[/cyan] (ID: {spec_id})")
        console.print(f"  File: {config.spectra_dir / 'specs' / f'{spec_id}.yaml'}")
        console.print(f"\n  Edit with: [cyan]spectra spec edit {spec_id}[/cyan]")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show")
def show_spec(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Display spec details."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Try to find spec
        spec = store.get_spec(spec_ref)
        if not spec:
            spec = store.get_spec_by_name(spec_ref)

        if not spec:
            console.print(f"[red]Error:[/red] Spec not found: {spec_ref}")
            raise typer.Exit(1)

        # Get YAML content
        yaml_content = store.get_spec_yaml(spec.id)

        # Display
        console.print(f"\n[bold cyan]{spec.name}[/bold cyan] ({spec.id})")
        console.print(f"State: [yellow]{spec.lifecycle_state}[/yellow]")
        console.print(f"Ceremony Level: {spec.ceremony_level}")
        console.print(f"Trust Score: {spec.trust_score:.2f}")
        console.print(f"\n[bold]Intent:[/bold]\n{spec.intent}\n")

        # Show metadata sections if present
        if spec.metadata:
            if "structure" in spec.metadata:
                console.print("[bold]Structure:[/bold]")
                structure = spec.metadata["structure"]
                if "files" in structure:
                    for f in structure["files"]:
                        console.print(f"  • {f}")

            if "acceptance" in spec.metadata:
                acceptance = spec.metadata["acceptance"]
                if "tests" in acceptance:
                    console.print("\n[bold]Acceptance Tests:[/bold]")
                    for test in acceptance["tests"]:
                        console.print(f"  • {test}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list")
def list_specs(
    state: Optional[str] = typer.Option(None, "--state", help="Filter by state"),
    level: Optional[int] = typer.Option(None, "--level", help="Filter by ceremony level"),
) -> None:
    """List all specs."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        specs = store.list_specs(state_filter=state, level_filter=level)
        edges = store.get_all_edges()

        if not specs:
            console.print("No specs found.")
            conn.close()
            return

        # Display as table
        table = to_rich_table(specs, edges)
        console.print(table)

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("edit")
def edit_spec(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Edit spec in $EDITOR."""
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

        # Get file path
        spec_path = config.spectra_dir / "specs" / f"{spec.id}.yaml"

        # Get editor
        import os
        editor = config.editor or os.environ.get("EDITOR", "vi")

        # Open in editor
        subprocess.run([editor, str(spec_path)])

        # Reload and update
        updated_node = parse_spec_file(spec_path)
        yaml_content = spec_path.read_text()
        store.update_spec(updated_node, yaml_content)

        console.print(f"[green]✓[/green] Updated spec: {spec.name}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("link")
def link_specs(
    source: str = typer.Argument(..., help="Source spec ID/name"),
    target: str = typer.Argument(..., help="Target spec ID/name"),
    edge_type: str = typer.Option("depends_on", "--type", help="Edge type"),
) -> None:
    """Create a link between two specs."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Find specs
        source_spec = store.get_spec(source) or store.get_spec_by_name(source)
        target_spec = store.get_spec(target) or store.get_spec_by_name(target)

        if not source_spec:
            console.print(f"[red]Error:[/red] Source spec not found: {source}")
            raise typer.Exit(1)

        if not target_spec:
            console.print(f"[red]Error:[/red] Target spec not found: {target}")
            raise typer.Exit(1)

        # Create edge
        edge = Edge(
            source_id=source_spec.id,
            target_id=target_spec.id,
            edge_type=EdgeType(edge_type),
        )
        store.create_edge(edge)

        console.print(
            f"[green]✓[/green] Linked {source_spec.name} → {target_spec.name} ({edge_type})"
        )

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("tree")
def show_tree(
    root: Optional[str] = typer.Argument(None, help="Root spec ID/name"),
) -> None:
    """Show dependency tree."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        specs = store.list_specs()
        edges = store.get_all_edges()

        engine = IntentGraphEngine()
        graph = engine.build_graph(specs, edges)

        if root:
            # Find root spec
            root_spec = store.get_spec(root) or store.get_spec_by_name(root)
            if not root_spec:
                console.print(f"[red]Error:[/red] Root spec not found: {root}")
                raise typer.Exit(1)
            root_id = root_spec.id
        else:
            root_id = None

        tree = to_rich_tree(graph, root_id)
        console.print(tree)

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("impact")
def impact_analysis(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Analyze impact of changing a spec."""
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

        # Build graph and analyze
        specs = store.list_specs()
        edges = store.get_all_edges()

        engine = IntentGraphEngine()
        engine.build_graph(specs, edges)

        report = engine.impact_analysis(spec.id)

        console.print(f"\n[bold]Impact Analysis for:[/bold] {spec.name}\n")
        console.print(f"Risk Level: [{_get_risk_color(report.risk_level)}]{report.risk_level}[/]")
        console.print(f"Total Affected Specs: {report.affected_count}")

        if report.direct_dependents:
            console.print(f"\n[bold]Direct Dependents ({len(report.direct_dependents)}):[/bold]")
            for dep_id in report.direct_dependents:
                dep_spec = store.get_spec(dep_id)
                if dep_spec:
                    console.print(f"  • {dep_spec.name} ({dep_id})")

        if report.transitive_dependents:
            console.print(f"\n[bold]Transitive Dependents ({len(report.transitive_dependents)}):[/bold]")
            for dep_id in report.transitive_dependents:
                dep_spec = store.get_spec(dep_id)
                if dep_spec:
                    console.print(f"  • {dep_spec.name} ({dep_id})")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("promote")
def promote_spec(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Promote spec to next lifecycle state."""
    try:
        from spectra.ceremony.enforcer import CeremonyEnforcer
        from spectra.constitution.engine import ConstitutionEngine
        from spectra.constitution.loader import get_active_constitution
        from spectra.lifecycle.promotion import LifecyclePromoter

        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")
        event_bus = EventBus(conn)

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

        # Load constitution
        constitution = get_active_constitution(config.to_dict())

        # Promote
        promoter = LifecyclePromoter(
            conn, event_bus, CeremonyEnforcer(), ConstitutionEngine()
        )

        transition = promoter.promote(
            spec.id, spec_data, "cli-user", constitution=constitution
        )

        console.print(
            f"[green]✓[/green] Promoted {spec.name}: "
            f"{transition.from_state.value} → {transition.to_state.value}"
        )

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("history")
def show_history(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Show lifecycle transition history."""
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

        # Get history
        transitions = lifecycle_history.get_history(conn, spec.id)

        if not transitions:
            console.print(f"No transition history for {spec.name}")
            conn.close()
            return

        console.print(f"\n[bold]Lifecycle History:[/bold] {spec.name}\n")

        for t in transitions:
            console.print(
                f"[dim]{t.timestamp.strftime('%Y-%m-%d %H:%M')}[/dim] "
                f"{t.from_state.value} → [cyan]{t.to_state.value}[/cyan]"
            )
            if t.reason:
                console.print(f"  Reason: {t.reason}")
            console.print()

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    colors = {
        "LOW": "green",
        "MEDIUM": "yellow",
        "HIGH": "orange",
        "CRITICAL": "red",
    }
    return colors.get(risk_level, "white")
