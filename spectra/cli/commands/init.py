"""Init command for creating new Spectra projects."""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from spectra.core.config import SpectraConfig, ensure_project_dirs, save_config
from spectra.core.database import get_connection, run_migrations

console = Console()


def init_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to initialize (default: current directory)",
    ),
    profile: str = typer.Option(
        "balanced",
        "--profile",
        "-p",
        help="Constitution profile (strict/balanced/rapid)",
    ),
) -> None:
    """Initialize a new Spectra project."""
    # Determine project root
    if path is None:
        project_root = Path.cwd()
    else:
        project_root = path.resolve()

    # Check if already initialized
    spectra_dir = project_root / ".spectra"
    if spectra_dir.exists():
        console.print(
            f"[yellow]Warning:[/yellow] .spectra/ already exists in {project_root}"
        )
        if not typer.confirm("Reinitialize?"):
            raise typer.Abort()

    console.print(f"Initializing Spectra project in [cyan]{project_root}[/cyan]")

    # Create directory structure
    console.print("Creating directory structure...")
    ensure_project_dirs(project_root)

    # Initialize database
    console.print("Creating database...")
    config = SpectraConfig(project_root=project_root)
    conn = get_connection(config.db_path)
    run_migrations(conn)
    conn.close()

    # Create config
    console.print("Creating configuration...")
    config.active_constitution_profile = profile
    save_config(config)

    # Copy constitution template
    console.print(f"Installing constitution profile: [cyan]{profile}[/cyan]")
    template_path = Path(__file__).parent.parent.parent / "templates" / "constitutions" / f"{profile}.yaml"

    if template_path.exists():
        constitution_path = spectra_dir / "constitution.yaml"
        shutil.copy(template_path, constitution_path)
    else:
        console.print(f"[yellow]Warning:[/yellow] Constitution template not found: {profile}")

    # Success message
    console.print()
    console.print(
        Panel(
            f"""[green]✓[/green] Spectra project initialized successfully!

[cyan]Project root:[/cyan] {project_root}
[cyan]Constitution:[/cyan] {profile}
[cyan]Database:[/cyan] {config.db_path}

[bold]Next steps:[/bold]
  1. Create your first spec: [cyan]spectra spec new my-feature[/cyan]
  2. View spec list: [cyan]spectra spec list[/cyan]
  3. Check ceremony level: [cyan]spectra ceremony check my-feature[/cyan]
""",
            title="Initialization Complete",
            border_style="green",
        )
    )
