
import pytest
from fastapi.testclient import TestClient
import sys
import os
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database import get_db, init_db

# Mock dependencies
from unittest.mock import MagicMock

# Create a temporary test database
TEST_DB_FILE = "test_internship.db"
TEST_APP_DIR = "test_applications"

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Cleanup test database and artifacts after all tests finish."""
    yield
    # Force garbage collection to release file handles
    import gc
    gc.collect()
    
    try:
        if os.path.exists(TEST_DB_FILE):
             os.remove(TEST_DB_FILE)
        if os.path.exists(TEST_APP_DIR):
            shutil.rmtree(TEST_APP_DIR, ignore_errors=True)
    except PermissionError:
        print(f"Warning: Could not delete {TEST_DB_FILE} - it fails on Windows sometimes.")
    except Exception as e:
        print(f"Cleanup error: {e}")

@pytest.fixture(scope="module")
def client():
    # Override database dependency
    import sqlite3
    
    def override_get_db():
        conn = sqlite3.connect(TEST_DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize Test DB
    with sqlite3.connect(TEST_DB_FILE) as conn:
        # Manually create table to avoid depending on schema.sql or non-test DB_NAME
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT,
                college TEXT,
                degree TEXT,
                github TEXT,
                kaggle_url TEXT,
                resume_path TEXT,
                parsed_resume_json TEXT,
                github_json TEXT,
                self_rating_json TEXT,
                application_id TEXT,
                overall_score REAL,
                score_breakdown_json TEXT
            );
        ''')

    # Override Directory creation logic in main.py is hardcoded to "applications/"
    # For now we will just let it write to applications/ and rely on cleanup or 
    # we would need to patch Path in main.py. 
    # To be safe and simple, we will just patch the external services.

    # Patch Email Service
    app.dependency_overrides["backend.email_service.send_confirmation_email"] = lambda *args: True
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_external_services(monkeypatch):
    """Mock external async services to avoid API calls."""
    
    async def mock_parse_resume(*args):
        return {"skills": ["Python", "FastAPI"], "education": "Test University"}
    
    async def mock_analyze_github(*args):
        return {"total_stars": 100, "public_repos": 5}
        
    def mock_send_email(*args):
        print("MOCK EMAIL SENT")
        return True

    monkeypatch.setattr("backend.main.parse_resume", mock_parse_resume)
    monkeypatch.setattr("backend.main.analyze_github", mock_analyze_github)
    monkeypatch.setattr("backend.main.send_confirmation_email", mock_send_email)

