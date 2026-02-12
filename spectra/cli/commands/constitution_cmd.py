"""Constitution management commands."""

import shutil
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from spectra.constitution.engine import ConstitutionEngine
from spectra.constitution.loader import load_builtin_profile, load_constitution
from spectra.constitution.schema import ConstitutionConfig
from spectra.core.config import load_config
from spectra.core.database import get_connection
from spectra.intent_graph.store import SpecStore

app = typer.Typer()
console = Console()


@app.command("init")
def init_constitution(
    profile: str = typer.Argument("balanced", help="Profile name (strict/balanced/rapid)"),
) -> None:
    """Initialize constitution from profile."""
    try:
        config = load_config()

        # Copy template
        template_path = Path(__file__).parent.parent.parent / "templates" / "constitutions" / f"{profile}.yaml"

        if not template_path.exists():
            console.print(f"[red]Error:[/red] Unknown profile: {profile}")
            raise typer.Exit(1)

        constitution_path = config.spectra_dir / "constitution.yaml"
        shutil.copy(template_path, constitution_path)

        # Update config
        config.active_constitution_profile = profile
        from spectra.core.config import save_config
        save_config(config)

        console.print(f"[green]✓[/green] Initialized constitution: [cyan]{profile}[/cyan]")
        console.print(f"  File: {constitution_path}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show")
def show_constitution() -> None:
    """Display active constitution rules."""
    try:
        config = load_config()
        constitution_path = config.spectra_dir / "constitution.yaml"

        if constitution_path.exists():
            constitution = load_constitution(constitution_path)
        else:
            profile = config.active_constitution_profile
            constitution = load_builtin_profile(profile)

        console.print(f"\n[bold]Constitution:[/bold] {constitution.profile}")
        console.print(f"Description: {constitution.description}\n")

        # Show settings
        console.print("[bold]Settings:[/bold]")
        console.print(f"  Strict Mode: {constitution.settings.strict_mode}")
        console.print(f"  Auto Fix: {constitution.settings.auto_fix}")
        console.print(f"  Ignore Archived: {constitution.settings.ignore_archived}\n")

        # Show rules
        table = Table(show_header=True)
        table.add_column("Rule")
        table.add_column("Type")
        table.add_column("Severity")
        table.add_column("Enabled", justify="center")

        for rule in constitution.rules:
            enabled_icon = "✓" if rule.enabled else "✗"
            table.add_row(
                rule.name,
                rule.type.value,
                rule.severity.value,
                enabled_icon,
            )

        console.print(table)
        console.print(f"\n[bold]Total Rules:[/bold] {len(constitution.rules)}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("enforce")
def enforce_constitution(
    spec_ref: Optional[str] = typer.Argument(None, help="Spec ID or name (optional)"),
) -> None:
    """Check spec(s) against constitution rules."""
    try:
        config = load_config()
        conn = get_connection(config.db_path)
        store = SpecStore(conn, config.spectra_dir / "specs")

        # Load constitution
        constitution_path = config.spectra_dir / "constitution.yaml"
        if constitution_path.exists():
            constitution = load_constitution(constitution_path)
        else:
            constitution = load_builtin_profile(config.active_constitution_profile)

        engine = ConstitutionEngine()

        if spec_ref:
            # Enforce on single spec
            spec = store.get_spec(spec_ref)
            if not spec:
                spec = store.get_spec_by_name(spec_ref)

            if not spec:
                console.print(f"[red]Error:[/red] Spec not found: {spec_ref}")
                raise typer.Exit(1)

            yaml_content = store.get_spec_yaml(spec.id)
            spec_data = yaml.safe_load(yaml_content)

            results = engine.enforce(spec_data, constitution)

            console.print(f"\n[bold]Constitution Enforcement:[/bold] {spec.name}\n")

            for result in results:
                if result.passed:
                    console.print(f"[green]✓[/green] {result.rule_name}")
                else:
                    severity_color = {
                        "error": "red",
                        "warning": "yellow",
                        "info": "blue",
                    }.get(result.severity.value, "white")
                    console.print(f"[{severity_color}]✗[/{severity_color}] {result.rule_name}: {result.message}")

            if engine.has_violations(results, constitution.settings.strict_mode):
                console.print("\n[red]Constitution violations found![/red]")
            else:
                console.print("\n[green]All rules satisfied![/green]")

        else:
            # Enforce on all specs
            specs = store.list_specs()
            violation_count = 0

            for spec in specs:
                yaml_content = store.get_spec_yaml(spec.id)
                spec_data = yaml.safe_load(yaml_content)
                results = engine.enforce(spec_data, constitution)

                if engine.has_violations(results, constitution.settings.strict_mode):
                    violation_count += 1
                    console.print(f"[red]✗[/red] {spec.name}: violations found")

            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  Total Specs: {len(specs)}")
            console.print(f"  Violations: {violation_count}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("profiles")
def list_profiles() -> None:
    """List available constitution profiles."""
    profiles = ["strict", "balanced", "rapid"]

    console.print("\n[bold]Available Constitution Profiles:[/bold]\n")

    for profile_name in profiles:
        constitution = load_builtin_profile(profile_name)
        console.print(f"[cyan]{profile_name}[/cyan]")
        console.print(f"  {constitution.description}")
        console.print(f"  Rules: {len(constitution.rules)}\n")
