from fastapi.testclient import TestClient
from app.main import app
import os
import sqlite3
from app.core.config import settings

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

def test_ui_routes():
    response = client.get("/operator")
    assert response.status_code == 200

    response = client.get("/contributor")
    assert response.status_code == 200

def test_snapshot_creation():
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    # Ensure a basic db file exists to be snapshotted
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.close()

    response = client.post("/sync/snapshot/create")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    snapshot_file = data["snapshot_file"]
    snapshot_path = os.path.join(os.path.dirname(db_path), snapshot_file)
    assert os.path.exists(snapshot_path)

    # Clean up
    os.remove(snapshot_path)
