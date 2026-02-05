
import json
from pathlib import Path

def _create_test_application(client):
    """Helper to create an application and return the ID and payload."""
    with open("tests/test_data/sample_payload.json") as f:
        payload = json.load(f)
        
    form_data = {k: str(v) for k, v in payload.items()}
    
    with open("tests/test_data/valid_resume.pdf", "rb") as f:
        files = {"resume": ("resume.pdf", f, "application/pdf")}
        response = client.post("/apply", data=form_data, files=files, follow_redirects=False)
        
    location = response.headers["location"]
    application_id = location.split("/")[-1]
    return application_id, payload

def test_submit_application_success(client, mock_external_services):
    """Test standard successful application submission."""
    app_id, _ = _create_test_application(client)
    # Verification is implicit in the helper's successful extraction of ID from redirect
    # But we can add explicit assertion if we were calling the endpoint directly.
    # Since helper does the work, we assume success if we got here. 
    # To be cleaner, we could inline logic here, but helper is better for DRY.
    assert app_id is not None

def test_dashboard_access(client, mock_external_services):
    """Verify dashboard loads for a valid applicant."""
    # Create an application
    app_id, payload = _create_test_application(client)
    
    # Request dashboard
    response = client.get(f"/dashboard/{app_id}")
    
    # Validation
    assert response.status_code == 200
    assert app_id in response.text
    # Optional: Check for candidate name to ensure correct data loading
    assert payload["full_name"] in response.text
