
import json
import pytest

def test_invalid_file_type(client):
    """Test validation rejection for non-PDF files."""
    
    with open("tests/test_data/sample_payload.json") as f:
        payload = json.load(f)
    form_data = {k: str(v) for k, v in payload.items()}
    
    # Upload text file instead of PDF
    with open("tests/test_data/invalid_resume.txt", "rb") as f:
        files = {"resume": ("resume.txt", f, "text/plain")}
        response = client.post("/apply", data=form_data, files=files)
        
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_missing_mandatory_fields(client):
    """Test submission fails when required fields are missing."""
    
    # Empty payload
    form_data = {}
    
    with open("tests/test_data/valid_resume.pdf", "rb") as f:
        files = {"resume": ("resume.pdf", f, "application/pdf")}
        response = client.post("/apply", data=form_data, files=files)
        
    # Expect 422 Unprocessable Entity
    assert response.status_code == 422

def test_invalid_application_id_access(client):
    """Test accessing a non-existent dashboard."""
    response = client.get("/dashboard/non-existent-id-12345")
    assert response.status_code == 404
    assert "Application not found" in response.json()["detail"]

def test_admin_login_wrong_credentials(client):
    """Test admin login failure with incorrect credentials."""
    response = client.post("/admin/login", data={"username": "wrong", "password": "badpassword"})
    
    # Should stay on the page and show error
    assert response.status_code == 200
    assert "Invalid credentials" in response.text
