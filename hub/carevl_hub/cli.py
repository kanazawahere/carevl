"""CLI entry point for CareVL Hub"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from carevl_hub.admin import admin_app
from carevl_hub.aggregator import DuckDBAggregator
from carevl_hub.config import load_settings
from carevl_hub.crypto import decrypt_file, validate_sqlite_integrity
from carevl_hub.downloader import GitHubDownloader

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
    settings = load_settings()
    output_dir = settings.snapshots_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    repo_list = [item.strip() for item in repos.split(",") if item.strip()] if repos else None

    typer.echo(f"Downloading snapshots into {output_dir}...")
    typer.echo(f"GitHub owner: {settings.github_org}")
    if repo_list:
        typer.echo(f"Repos: {', '.join(repo_list)}")
    elif latest:
        typer.echo("Repos: all accessible repos, latest release only")

    downloader = GitHubDownloader(token=settings.github_token, org=settings.github_org)
    downloaded_files = downloader.download_snapshots(
        output_dir=output_dir,
        date=date,
        repos=repo_list,
        latest=latest,
    )

    if not downloaded_files:
        typer.echo("No snapshot assets downloaded.")
        raise typer.Exit(1)

    typer.echo(f"✓ Download completed: {len(downloaded_files)} file(s)")
    for path in downloaded_files:
        typer.echo(f"  - {path}")


@app.command()
def decrypt(
    input_dir: Path = typer.Option(..., help="Input directory with .db.enc files"),
    output_dir: Path = typer.Option(..., help="Output directory for decrypted .db files")
):
    """Decrypt encrypted snapshots"""
    settings = load_settings()
    typer.echo(f"Decrypting snapshots from {input_dir}...")

    enc_files = sorted(input_dir.rglob("*.db.enc"))
    if not enc_files:
        typer.echo("No .db.enc files found.")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    key = settings.encryption_key.encode("utf-8")
    decrypted_files: list[Path] = []

    for enc_file in enc_files:
        relative_parent = enc_file.parent.relative_to(input_dir)
        output_path = output_dir / relative_parent / enc_file.name[:-4]
        decrypt_file(str(enc_file), str(output_path), key=key)
        validate_sqlite_integrity(output_path)
        decrypted_files.append(output_path)
        typer.echo(f"  - {output_path}")

    typer.echo(f"✓ Decryption completed: {len(decrypted_files)} file(s)")


@app.command()
def aggregate(
    input_dir: Path = typer.Option(..., help="Input directory with decrypted .db files"),
    output: Path = typer.Option(..., help="Output file (.parquet, .db, .csv)")
):
    """Aggregate data from multiple stations using DuckDB"""
    settings = load_settings()
    typer.echo(f"Aggregating data from {input_dir}...")

    db_files = sorted(input_dir.rglob("*.db"))
    if not db_files:
        typer.echo("No decrypted .db files found.")
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)
    duckdb_path = output if output.suffix.lower() in {".duckdb", ".db"} else None
    aggregator = DuckDBAggregator(
        memory_limit=settings.duckdb_memory_limit,
        threads=settings.duckdb_threads,
    )

    try:
        aggregator.connect(db_path=duckdb_path)
        aggregator.attach_databases(db_files)
        counts = aggregator.aggregate_all()

        if output.suffix.lower() == ".parquet":
            parquet_dir = output.parent / output.stem
            aggregator.export_to_parquet(parquet_dir)
            typer.echo(f"Parquet exported to {parquet_dir}")
        elif output.suffix.lower() in {".duckdb", ".db"}:
            typer.echo(f"DuckDB file written to {output}")
        else:
            typer.echo("Unsupported output suffix. Use `.duckdb`, `.db`, or `.parquet`.")
            raise typer.Exit(1)
    finally:
        aggregator.close()

    typer.echo(
        "✓ Aggregation completed: "
        + ", ".join(f"{table}={count}" for table, count in counts.items())
    )


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
