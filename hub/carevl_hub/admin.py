"""Hub Admin tools for station provisioning"""

import json
import base64
import csv
from pathlib import Path
from typing import Optional
import typer

admin_app = typer.Typer(
    name="admin",
    help="Hub Admin tools for managing stations"
)


def encode_invite_code(
    station_id: str,
    station_name: str,
    repo_url: str,
    pat: str,
    encryption_key: Optional[str] = None
) -> str:
    """
    Encode station data into invite code
    
    Args:
        station_id: Unique station identifier (e.g., TRAM_001)
        station_name: Display name (e.g., Trạm Y Tế Xã A)
        repo_url: GitHub repository URL
        pat: GitHub Personal Access Token (fine-grained)
        encryption_key: Optional encryption key for snapshots
    
    Returns:
        Base64 encoded invite code
    """
    data = {
        "station_id": station_id,
        "station_name": station_name,
        "repo_url": repo_url,
        "pat": pat
    }
    
    if encryption_key:
        data["encryption_key"] = encryption_key
    
    json_str = json.dumps(data, ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    return encoded


@admin_app.command("generate-code")
def generate_single_code(
    station_id: str = typer.Option(..., help="Station ID (e.g., TRAM_001)"),
    station_name: str = typer.Option(..., help="Station name (e.g., Trạm Y Tế Xã A)"),
    repo_url: str = typer.Option(..., help="GitHub repo URL"),
    pat: str = typer.Option(..., help="GitHub PAT (fine-grained)"),
    encryption_key: Optional[str] = typer.Option(None, help="Encryption key (optional)"),
    output: Optional[Path] = typer.Option(None, help="Save to file instead of stdout")
):
    """Generate single invite code for a station"""
    
    invite_code = encode_invite_code(
        station_id=station_id,
        station_name=station_name,
        repo_url=repo_url,
        pat=pat,
        encryption_key=encryption_key
    )
    
    if output:
        output.write_text(invite_code)
        typer.echo(f"✓ Invite code saved to: {output}")
    else:
        typer.echo("\n" + "=" * 60)
        typer.echo(f"Station: {station_name} ({station_id})")
        typer.echo("=" * 60)
        typer.echo(f"\nInvite Code:\n{invite_code}\n")
        typer.echo("=" * 60)
        typer.echo("\nSend this code to station via Zalo/Email")


@admin_app.command("generate-batch")
def generate_batch_codes(
    input_csv: Path = typer.Option(..., help="CSV file with station data"),
    output_dir: Path = typer.Option("./invite_codes", help="Output directory for codes")
):
    """
    Generate invite codes from CSV file
    
    CSV format:
    station_id,station_name,repo_url,pat,encryption_key
    TRAM_001,Trạm Y Tế Xã A,https://github.com/org/station-001,ghp_xxx,key1
    TRAM_002,Trạm Y Tế Xã B,https://github.com/org/station-002,ghp_yyy,key2
    """
    
    if not input_csv.exists():
        typer.echo(f"❌ File not found: {input_csv}", err=True)
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            station_id = row['station_id']
            station_name = row['station_name']
            repo_url = row['repo_url']
            pat = row['pat']
            encryption_key = row.get('encryption_key', None)
            
            if encryption_key == '':
                encryption_key = None
            
            invite_code = encode_invite_code(
                station_id=station_id,
                station_name=station_name,
                repo_url=repo_url,
                pat=pat,
                encryption_key=encryption_key
            )
            
            # Save to individual file
            code_file = output_dir / f"{station_id}_invite_code.txt"
            code_file.write_text(invite_code)
            
            typer.echo(f"✓ Generated: {station_id} -> {code_file}")
            count += 1
    
    typer.echo(f"\n✓ Generated {count} invite codes in: {output_dir}")


@admin_app.command("create-csv-template")
def create_csv_template(
    output: Path = typer.Option("stations_template.csv", help="Output CSV file")
):
    """Create CSV template for batch generation"""
    
    template = """station_id,station_name,repo_url,pat,encryption_key
TRAM_001,Trạm Y Tế Xã A,https://github.com/carevl-bot/station-001,ghp_xxxxxxxxxxxx,optional-key-1
TRAM_002,Trạm Y Tế Xã B,https://github.com/carevl-bot/station-002,ghp_yyyyyyyyyyyy,optional-key-2
TRAM_003,Trạm Y Tế Xã C,https://github.com/carevl-bot/station-003,ghp_zzzzzzzzzzzz,
"""
    
    output.write_text(template, encoding='utf-8')
    typer.echo(f"✓ Template created: {output}")
    typer.echo("\nEdit this file with your station data, then run:")
    typer.echo(f"  carevl-hub admin generate-batch --input-csv {output}")


@admin_app.command("operator-checklist")
def operator_checklist():
    """Print Hub Admin checklist for E2E step 1 (repos, PATs, invite codes)."""
    typer.echo(
        """
CareVL Hub Admin — checklist (E2E step 1)
1. GitHub bot account + one repo per station (fine-grained PAT: Contents read/write).
2. Generate PAT manually in GitHub UI (fine-grained PAT cannot be created via API).
3. carevl-hub admin generate-code --station-id ... --station-name ... --repo-url ... --pat ...
   Or: admin generate-batch --input-csv stations.csv --output-dir ./invite_codes
4. Send each invite code to the station (Zalo / Email).
5. Optional: admin validate-code <paste> — sanity-check before sending.

Edge step 2–3: station runs bootstrap, opens /provision/, pastes invite, New or Restore, sets PIN.
"""
    )


@admin_app.command("validate-code")
def validate_code(
    invite_code: str = typer.Argument(..., help="Invite code to validate")
):
    """Validate and decode invite code"""
    
    try:
        # Decode Base64
        decoded_bytes = base64.urlsafe_b64decode(invite_code.encode('utf-8'))
        json_str = decoded_bytes.decode('utf-8')
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Validate required fields
        required = ['station_id', 'station_name', 'repo_url', 'pat']
        missing = [f for f in required if f not in data]
        
        if missing:
            typer.echo(f"❌ Missing required fields: {', '.join(missing)}", err=True)
            raise typer.Exit(1)
        
        # Display decoded data
        typer.echo("\n✓ Valid invite code")
        typer.echo("=" * 60)
        typer.echo(f"Station ID: {data['station_id']}")
        typer.echo(f"Station Name: {data['station_name']}")
        typer.echo(f"Repo URL: {data['repo_url']}")
        typer.echo(f"PAT: {data['pat'][:10]}... (hidden)")
        
        if 'encryption_key' in data and data['encryption_key']:
            typer.echo(f"Encryption Key: {data['encryption_key'][:10]}... (hidden)")
        else:
            typer.echo("Encryption Key: (not provided)")
        
        typer.echo("=" * 60)
        
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        typer.echo(f"❌ Invalid Base64 encoding: {e}", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo(f"❌ Invalid JSON format: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    admin_app()
