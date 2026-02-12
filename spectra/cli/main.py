"""Main CLI entry point for Spectra."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from spectra import __version__

# Create main app
app = typer.Typer(
    name="spectra",
    help="Intent-driven development orchestration system",
    no_args_is_help=True,
)

console = Console()


# Global options
@app.callback()
def main(
    ctx: typer.Context,
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (auto-detect if not specified)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Spectra CLI - Intent-driven development orchestration."""
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["project_dir"] = project_dir
    ctx.obj["verbose"] = verbose
    ctx.obj["json_output"] = json_output


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"Spectra version {__version__}")


# Register command groups
from spectra.cli.commands import ceremony_cmd, constitution_cmd, init, specify

app.add_typer(specify.app, name="spec", help="Manage specs")
app.add_typer(ceremony_cmd.app, name="ceremony", help="Ceremony level management")
app.add_typer(constitution_cmd.app, name="const", help="Constitution management")
app.command()(init.init_command)


# Error handling
def handle_error(e: Exception) -> None:
    """Display error in a nice format."""
    console.print(
        Panel(
            f"[red]{type(e).__name__}:[/red] {str(e)}",
            title="Error",
            border_style="red",
        )
    )
    sys.exit(1)


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        handle_error(e)
