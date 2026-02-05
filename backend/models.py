from pydantic import BaseModel, EmailStr
from typing import Optional, Any
import json

class ApplicantCreate(BaseModel):
    full_name: str
    email: EmailStr
    college: str
    degree: str
    github: str
    portfolio: str
    programming: int
    data_structures: int
    machine_learning: int
    web_development: int
    git_tools: int

class ApplicantResponse(BaseModel):
    id: int
    full_name: str
    email: str
    college: str
    degree: str
    github: str
    resume_path: Optional[str] = None
    parsed_resume_json: Optional[Any] = None
    github_json: Optional[Any] = None
    application_id: str

    class Config:
        from_attributes = True

    # Helper validators or pre-processors could act here to parse the JSON strings from DB if needed,
    # but for now we'll stick to basic definitions. 
    # If the DB stores JSON as text, the response model might expect dicts if we parse them before response,
    # or strings if we just return raw. 
    # Usually better to clarify. I will assume they might be passed as strings or dicts. 
    # Let's set types to Any to be safe or Optional[dict] if we process them.
