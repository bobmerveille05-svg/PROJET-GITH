"""Fast-track fix command for patch-level changes."""

import typer
from rich.console import Console

console = Console()
app = typer.Typer()


@app.command()
def fix_command(
    spec_ref: str = typer.Argument(..., help="Spec ID or name"),
) -> None:
    """Fast-track a patch fix with minimal ceremony."""
    console.print(f"[yellow]Note:[/yellow] Fix command coming in Phase 2")
    console.print("For now, use: spectra spec promote <spec>")
