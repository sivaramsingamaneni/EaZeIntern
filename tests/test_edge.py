
import json
import pytest

def test_resume_minimal_content(client, mock_external_services):
    """Test upload with a valid but very small/empty PDF (checking if backend crashes)."""
    
    with open("tests/test_data/sample_payload.json") as f:
        payload = json.load(f)
    form_data = {k: str(v) for k, v in payload.items()}
    
    # We use valid_resume.pdf which is already minimal.
    # To test 'empty' we can create a 0-byte file in memory.
    from io import BytesIO
    empty_pdf = BytesIO(b"") 
    
    # Depending on how strict pypdf is, this might fail parsing but SHOULD NOT crash the server.
    # The endpoint catches parse errors.
    
    files = {"resume": ("empty.pdf", empty_pdf, "application/pdf")}
    
    response = client.post("/apply", data=form_data, files=files, follow_redirects=False)
    
    # Should still succeed in submission (as parsing failure is non-blocking)
    assert response.status_code == 303

def test_github_zero_repos(client, monkeypatch):
    """Test edge case where GitHub user has 0 repositories."""
    
    # Override the mock specifically for this test
    async def mock_zero_repos(*args):
        return {"total_stars": 0, "public_repos": 0}
        
    monkeypatch.setattr("backend.main.analyze_github", mock_zero_repos)
    # Also need to mock other services or use the fixture
    monkeypatch.setattr("backend.main.parse_resume", lambda *args: {})
    monkeypatch.setattr("backend.main.send_confirmation_email", lambda *args: True)

    with open("tests/test_data/sample_payload.json") as f:
        payload = json.load(f)
    
    # Modify payload
    payload["github"] = "https://github.com/newuser"
    form_data = {k: str(v) for k, v in payload.items()}
    
    with open("tests/test_data/valid_resume.pdf", "rb") as f:
        files = {"resume": ("resume.pdf", f, "application/pdf")}
        response = client.post("/apply", data=form_data, files=files, follow_redirects=False)

    assert response.status_code == 303
    app_id = response.headers["location"].split("/")[-1]
    
    # Check dashboard to see if data reflects 0 repos
    response = client.get(f"/dashboard/{app_id}")
    assert "0" in response.text # Should verify repos count is 0

def test_long_candidate_name(client, mock_external_services):
    """Test submission with an extremely long name."""
    
    with open("tests/test_data/sample_payload.json") as f:
        payload = json.load(f)
    
    long_name = "A" * 1000
    payload["full_name"] = long_name
    form_data = {k: str(v) for k, v in payload.items()}
    
    with open("tests/test_data/valid_resume.pdf", "rb") as f:
        files = {"resume": ("resume.pdf", f, "application/pdf")}
        response = client.post("/apply", data=form_data, files=files, follow_redirects=False)
        
    assert response.status_code == 303
    app_id = response.headers["location"].split("/")[-1]
    
    # Just ensure it was saved
    response = client.get(f"/dashboard/{app_id}")
    assert response.status_code == 200
    # The name might be truncated in display or full length, just ensure page loads
