import uuid

def generate_application_id() -> str:
    """Generates a unique application ID."""
    return str(uuid.uuid4())
