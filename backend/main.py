from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil
import json
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Local imports
import sys
# Add the project root directory to sys.path so 'backend' module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db, init_db, create_applicant
from backend.resume_parser import parse_resume
from backend.github_service import analyze_github
from backend.email_service import send_confirmation_email
from backend.utils import generate_application_id
from backend.scoring import calculate_score

app = FastAPI()

# Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "fallback_secret_key"))

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/applications", StaticFiles(directory="applications"), name="applications")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def landing_page(request: Request):
    """Serves the main landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/apply")
def form_page(request: Request):
    """Serves the application form."""
    return templates.TemplateResponse("apply.html", {"request": request})

@app.get("/track")
def track_page(request: Request):
    """Serves the tracking page."""
    return templates.TemplateResponse("track.html", {"request": request})

@app.post("/track")
async def track_application(request: Request, application_id: str = Form(...), db = Depends(get_db)):
    """Handles tracking form submission."""
    # sanitization
    application_id = application_id.strip()
    
    cursor = db.cursor()
    cursor.execute("SELECT id FROM applicants WHERE application_id = ?", (application_id,))
    if cursor.fetchone():
        return RedirectResponse(url=f"/dashboard/{application_id}", status_code=303)
    else:
        return templates.TemplateResponse("track.html", {
            "request": request,
            "error": "Invalid Application ID. Please check and try again.",
            "application_id": application_id
        })

@app.post("/apply")
async def submit_application(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    college: str = Form(...),
    degree: str = Form(...),
    github: str = Form(...),
    kaggle: str = Form(...),
    skill_prog: int = Form(...),
    skill_dsa: int = Form(...),
    skill_ml: int = Form(...),
    skill_web: int = Form(...),
    skill_tools: int = Form(...),
    resume: UploadFile = File(...),
    db = Depends(get_db)
):
    try:
        # Validate file type
        if resume.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # 1. Generate unique application_id
        application_id = generate_application_id()

        # 2. Creates application folder safely
        # Ensure the 'applications' parent directory exists
        try:
            app_folder = Path(f"applications/{application_id}")
            app_folder.mkdir(parents=True, exist_ok=True)
            
            # Save resume
            resume_path = app_folder / "resume.pdf"
            with open(resume_path, "wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)
        except Exception as e:
            print(f"Filesystem Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to save application files.")

        # 3. Store in SQLite FIRST (User data safety)
        # We start with empty JSONs for the optional fields so we satisfy the "save first" requirement
        # and ensure constraints are met.
        
        self_ratings = {
            "Programming": skill_prog,
            "DSA": skill_dsa,
            "ML_AI": skill_ml,
            "Web_Dev": skill_web,
            "Tools": skill_tools
        }

        # Safe defaults
        parsed_resume_data = {}
        github_data = {}

        try:
            create_applicant(db, (
                full_name,
                email,
                college,
                degree,
                github,
                kaggle,
                str(resume_path),
                json.dumps(parsed_resume_data), # Initially empty
                json.dumps(github_data),        # Initially empty
                json.dumps(self_ratings),
                application_id,
                0.0,             # Initial overall_score
                json.dumps({})   # Initial score_breakdown
            ))
        except Exception as e:
            print(f"Database Insert Error: {e}")
            raise HTTPException(status_code=500, detail="Database insertion failed.")

        # 4. Parse Resume safely (Non-blocking failure)
        try:
            # parse_resume is async, so proper await usage is critical
            parsed_resume_data = await parse_resume(str(resume_path))
        except Exception as e:
            print(f"Resume Parsing Failed for {application_id}: {e}")
            parsed_resume_data = {"error": "Resume parsing failed", "details": str(e)}

        # 5. Analyze GitHub safely (Non-blocking failure)
        try:
            # Extract username from URL if needed
            github_username = github.split("/")[-1] if "github.com" in github else github
            # analyze_github is async
            github_data = await analyze_github(github_username)
        except Exception as e:
            print(f"GitHub Analysis Failed for {application_id}: {e}")
            github_data = {"error": "GitHub analysis failed", "details": str(e)}

        # 6. Update Database with enriched data
        # Calculate Score
        try:
            score_result = calculate_score(self_ratings, parsed_resume_data, github_data)
            print(f"DEBUG: Score Result for {application_id}: {score_result}")
            overall_score = score_result.get("overall_score", 0)
            score_breakdown = score_result.get("breakdown", {})
        except Exception as e:
            print(f"Scoring Failed for {application_id}: {e}")
            overall_score = 0
            score_breakdown = {}

        # We perform an UPDATE now that we have (potentially) enriched data
        # CRITICAL: We store the entire parsed_resume_data as a JSON string.
        # This preserves all fields (name, email, skills, education, experience) without data loss.
        try:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE applicants 
                SET parsed_resume_json = ?, github_json = ?, overall_score = ?, score_breakdown_json = ?
                WHERE application_id = ?
            """, (
                json.dumps(parsed_resume_data, default=str), 
                json.dumps(github_data, default=str), 
                overall_score,
                json.dumps(score_breakdown),
                application_id
            ))
            db.commit()
        except Exception as e:
            print(f"Database Update Failed for {application_id}: {e}")
            # We do NOT raise here, because the application is already submitted successfully.
            # The user can still see their dashboard, just without enriched data.

        # 6.5 Save Full Profile JSON to Disk
        try:
            full_profile = {
                "application_id": application_id,
                "full_name": full_name,
                "email": email,
                "college": college,
                "degree": degree,
                "github": github,
                "kaggle": kaggle,
                "self_ratings": self_ratings,
                "parsed_resume": parsed_resume_data,
                "github_analysis": github_data,
                "resume_path": str(resume_path)
            }
            
            profile_path = app_folder / "profile.json"
            with open(profile_path, "w", encoding='utf-8') as f:
                json.dump(full_profile, f, indent=4, default=str)
                
            print(f"✅ Profile JSON saved to {profile_path}")
            
        except Exception as e:
            print(f"Failed to save profile.json for {application_id}: {e}")


        # 7. Send confirmation email safely
        try:
            print(f"DEBUG: Triggering email for {email}")
            send_confirmation_email(email, application_id)
        except Exception as e:
            print(f"Email sending failed for {application_id}: {e}")
            # Fail silently regarding the response to user; logging is sufficient.

        # 8. Redirect to dashboard
        return RedirectResponse(url=f"/dashboard/{application_id}", status_code=303)

    except HTTPException as he:
        # Re-raise HTTP exceptions as is
        raise he
    except Exception as e:
        # Catch-all for any other unexpected errors to prevent 500 crash without logging
        print(f"Unexpected Error in submit_application: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during application processing.")

@app.get("/dashboard/{application_id}")
async def dashboard(request: Request, application_id: str, db = Depends(get_db)):
    """User dashboard to view their application status."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM applicants WHERE application_id = ?", (application_id,))
    applicant = cursor.fetchone()
    
    if not applicant:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Parse JSON strings back to dicts for the template
    # This ensures the full resume structure is passed to the frontend
    applicant_dict = dict(applicant)
    if applicant_dict.get("parsed_resume_json"):
        try:
            applicant_dict["parsed_resume"] = json.loads(applicant_dict["parsed_resume_json"])
        except json.JSONDecodeError:
            applicant_dict["parsed_resume"] = {}

    if applicant_dict.get("github_json"):
        try:
            applicant_dict["github_data"] = json.loads(applicant_dict["github_json"])
        except json.JSONDecodeError:
            applicant_dict["github_data"] = {}
            
    if applicant_dict.get("self_rating_json"):
        try:
            applicant_dict["self_ratings"] = json.loads(applicant_dict["self_rating_json"])
        except json.JSONDecodeError:
            applicant_dict["self_ratings"] = {}
        
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request, 
        "applicant": applicant_dict
    })

@app.get("/admin/applicant/{application_id}")
async def admin_applicant_detail(request: Request, application_id: str, db = Depends(get_db)):
    """View detailed applicant info by Application ID."""
    # Check session
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)

    cursor = db.cursor()
    cursor.execute("SELECT * FROM applicants WHERE application_id = ?", (application_id,))
    applicant = cursor.fetchone()
    
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    app_dict = dict(applicant)

    # Helper function to safely parse JSON or return default
    def safe_json_load(json_str, default):
        if not json_str:
            return default
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return default

    # Parse JSON fields
    app_dict["parsed_resume"] = safe_json_load(app_dict.get("parsed_resume_json"), {})
    app_dict["github_data"] = safe_json_load(app_dict.get("github_json"), {})
    app_dict["self_ratings"] = safe_json_load(app_dict.get("self_rating_json"), {})
    app_dict["score_breakdown"] = safe_json_load(app_dict.get("score_breakdown_json"), {})

    return templates.TemplateResponse("admin_applicant_detail.html", {
        "request": request,
        "applicant": app_dict
    })

@app.get("/admin/login")
def admin_login_page(request: Request):
    """Serves the admin login page."""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handles admin login."""
    # Use load_dotenv() at startup to ensure os.getenv works, but we also re-read it here safely
    # Strip whitespace to prevent issues
    env_user = os.getenv("ADMIN_USERNAME", "").strip()
    env_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    
    # Input sanitization
    username = username.strip()
    password = password.strip()
    
    # DEBUG LOG (Remove in production)
    print(f"DEBUG: Login Attempt - Username: '{username}' Matches Env: {username == env_user}")
    print(f"DEBUG: Env Loaded check - User: {bool(env_user)}, Pass: {bool(env_pass)}")
    
    if env_user and env_pass and username == env_user and password == env_pass:
        request.session["admin_logged_in"] = True
        return RedirectResponse(url="/admin", status_code=303)
    else:
         return templates.TemplateResponse("admin_login.html", {
            "request": request, 
            "error": "Invalid credentials"
        })

@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Logs out the admin."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin")
async def admin_dashboard(request: Request, db = Depends(get_db)):
    """Admin dashboard to view all applicants."""
    # Check session
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    
    cursor = db.cursor()
    # Order by overall_score DESC (NULLs last logic implicitly handled or we accept NULLs first/last depending on DB)
    # Using simple ORDER BY overall_score DESC usually puts NULLs last in SQLite.
    cursor.execute("SELECT * FROM applicants ORDER BY overall_score DESC")
    applicants = cursor.fetchall()
    
    # Process data for the list view
    processed_applicants = []
    for app in applicants:
        app_dict = dict(app)
        
        # Handle Score Display
        score = app_dict.get("overall_score")
        if score is not None:
             app_dict["overall_score"] = round(float(score), 1)
        else:
             app_dict["overall_score"] = "N/A"

        # 1. Parse Resume Data
        if app_dict.get("parsed_resume_json"):
            try:
                resume_data = json.loads(app_dict["parsed_resume_json"])
                app_dict["parsed_resume"] = resume_data # Fully parsed for detailed view
                app_dict["skills_preview"] = ", ".join(resume_data.get("skills", [])[:5])
            except json.JSONDecodeError:
                app_dict["parsed_resume"] = {}
                app_dict["skills_preview"] = "Data Error"
        else:
            app_dict["parsed_resume"] = {}
            app_dict["skills_preview"] = "Processing..."
            
        # 2. Parse GitHub Data
        if app_dict.get("github_json"):
            try:
                gh_data = json.loads(app_dict["github_json"])
                app_dict["github_data"] = gh_data # Fully parsed for detailed view
                app_dict["gh_stars"] = gh_data.get("total_stars", 0)
                app_dict["gh_repos"] = gh_data.get("public_repos", 0)
            except json.JSONDecodeError:
                app_dict["github_data"] = {}
                app_dict["gh_stars"] = "-"
                app_dict["gh_repos"] = "-"  
        else:
            app_dict["github_data"] = {}
            app_dict["gh_stars"] = "-"
            app_dict["gh_repos"] = "-"

        # 3. Parse Self Ratings
        if app_dict.get("self_rating_json"):
            try:
                app_dict["self_ratings"] = json.loads(app_dict["self_rating_json"])
            except json.JSONDecodeError:
                 app_dict["self_ratings"] = {}
        else:
            app_dict["self_ratings"] = {}
            
        processed_applicants.append(app_dict)

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request, 
        "applicants": processed_applicants
    })

@app.get("/admin/export/json")
async def admin_export_json(request: Request, db = Depends(get_db)):
    """Export all candidates as a JSON file."""
    # Check session
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)

    cursor = db.cursor()
    cursor.execute("SELECT * FROM applicants ORDER BY application_id")
    applicants = cursor.fetchall()

    export_data = []
    for app in applicants:
        app_dict = dict(app)
        
        # Helper to parse JSON fields safely
        def parse_field(field_name):
            try:
                content = app_dict.get(field_name)
                return json.loads(content) if content else {}
            except json.JSONDecodeError:
                return {}

        # Construct structured export object
        export_item = {
            "application_id": app_dict["application_id"],
            "full_name": app_dict["full_name"],
            "email": app_dict["email"],
            "college": app_dict["college"],
            "degree": app_dict["degree"],
            "github_profile": app_dict["github"],
            "kaggle_profile": app_dict["kaggle"],
            "resume_path": app_dict["resume_path"],
            "overall_score": app_dict["overall_score"],
            "self_ratings": parse_field("self_rating_json"),
            "parsed_resume": parse_field("parsed_resume_json"),
            "github_analysis": parse_field("github_json"),
            "score_breakdown": parse_field("score_breakdown_json"),
            "created_at": app_dict["created_at"]
        }
        export_data.append(export_item)

    # Generate filename with date
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"eazeintern_candidates_{date_str}.json"
    
    # Return as downloadable file
    from fastapi import Response
    json_content = json.dumps(export_data, indent=4, default=str)
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Backend Server...")
    # reload=True works best when run as a module, but often works in script too
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
