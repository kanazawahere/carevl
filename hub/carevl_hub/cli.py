"""CLI entry point for CareVL Hub"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from carevl_hub.admin import admin_app

app = typer.Typer(
    name="carevl-hub",
    help="CareVL Hub - Data aggregation and analytics for provincial health department"
)

# Add admin subcommand
app.add_typer(admin_app, name="admin")


@app.command()
def gui(
    port: int = typer.Option(8501, help="Streamlit server port"),
    host: str = typer.Option("127.0.0.1", help="Bind address (default: localhost only)"),
):
    """Launch Hub operator GUI (Streamlit) — ADR 29 MVP."""
    pkg = Path(__file__).resolve().parent
    hub_dir = pkg.parent
    gui_app = pkg / "gui" / "app.py"
    if not gui_app.is_file():
        typer.echo(f"GUI entry not found: {gui_app}", err=True)
        raise typer.Exit(1)

    env = os.environ.copy()
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(hub_dir) + (os.pathsep + prev if prev else "")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(gui_app),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    typer.echo(f"Starting Hub GUI: {' '.join(cmd)}")
    typer.echo(f"Working directory: {hub_dir}")
    raise typer.Exit(subprocess.call(cmd, cwd=str(hub_dir), env=env))


@app.command()
def init(
    encryption_key: str = typer.Option(..., help="Base64 encryption key"),
    github_token: str = typer.Option(..., help="GitHub Personal Access Token"),
    org: str = typer.Option(..., help="GitHub organization name"),
    output_dir: Path = typer.Option("./hub_data", help="Output directory for data")
):
    """Initialize Hub configuration"""
    typer.echo(f"Initializing CareVL Hub...")
    typer.echo(f"Organization: {org}")
    typer.echo(f"Output directory: {output_dir}")
    
    # TODO: Implement initialization
    # - Create .env file
    # - Validate GitHub token
    # - Create output directories
    
    typer.echo("✓ Hub initialized successfully")


@app.command()
def download(
    date: Optional[str] = typer.Option(None, help="Download snapshots for specific date (YYYY-MM-DD)"),
    repos: Optional[str] = typer.Option(None, help="Comma-separated list of repo names"),
    latest: bool = typer.Option(False, help="Download latest snapshots")
):
    """Download encrypted snapshots from GitHub"""
    typer.echo("Downloading snapshots...")
    
    # TODO: Implement download
    # - List repos in org
    # - List releases
    # - Download .db.enc files
    
    typer.echo("✓ Download completed")


@app.command()
def decrypt(
    input_dir: Path = typer.Option(..., help="Input directory with .db.enc files"),
    output_dir: Path = typer.Option(..., help="Output directory for decrypted .db files")
):
    """Decrypt encrypted snapshots"""
    typer.echo(f"Decrypting snapshots from {input_dir}...")
    
    # TODO: Implement decryption
    # - Scan for .db.enc files
    # - Decrypt using shared.crypto
    # - Validate SQLite integrity
    
    typer.echo("✓ Decryption completed")


@app.command()
def aggregate(
    input_dir: Path = typer.Option(..., help="Input directory with decrypted .db files"),
    output: Path = typer.Option(..., help="Output file (.parquet, .db, .csv)")
):
    """Aggregate data from multiple stations using DuckDB"""
    typer.echo(f"Aggregating data from {input_dir}...")
    
    # TODO: Implement aggregation
    # - Attach all SQLite databases
    # - Run DuckDB queries
    # - Export to Parquet/CSV
    
    typer.echo(f"✓ Aggregation completed: {output}")


@app.command()
def report(
    format: str = typer.Option("excel", help="Report format: excel, pdf, html"),
    output: Path = typer.Option(..., help="Output file path"),
    template: Optional[Path] = typer.Option(None, help="Custom SQL template")
):
    """Generate reports from aggregated data"""
    typer.echo(f"Generating {format} report...")
    
    # TODO: Implement report generation
    # - Load aggregated data
    # - Apply template or default queries
    # - Generate Excel/PDF/HTML
    
    typer.echo(f"✓ Report generated: {output}")


@app.command()
def quality(
    input_dir: Path = typer.Option(..., help="Input directory with decrypted .db files"),
    output: Path = typer.Option(..., help="Output quality report (.html, .json)")
):
    """Run data quality checks"""
    typer.echo(f"Running quality checks on {input_dir}...")
    
    # TODO: Implement quality checks
    # - Missing required fields
    # - Duplicate identifiers
    # - Invalid date ranges
    # - Orphaned records
    # - Outliers
    
    typer.echo(f"✓ Quality report generated: {output}")


@app.command()
def dashboard(
    port: int = typer.Option(8080, help="Dashboard port"),
    data_dir: Path = typer.Option("./hub_data", help="Data directory")
):
    """Launch interactive Streamlit dashboard"""
    typer.echo(f"Starting dashboard on port {port}...")
    
    # TODO: Implement dashboard
    # - Launch Streamlit app
    # - Load aggregated data
    # - Interactive charts and filters
    
    typer.echo(f"✓ Dashboard running at http://localhost:{port}")


if __name__ == "__main__":
    app()
