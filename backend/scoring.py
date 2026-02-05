from datetime import datetime
import math

def calculate_score(self_ratings: dict, resume_data: dict, github_data: dict) -> dict:
    """
    Calculates the candidate score based on:
    1. Skill Self-Ratings (Max 40 points)
    2. Resume Analysis (Max 30 points)
    3. GitHub Analysis (Max 30 points)
    
    Total Score is capped at 100.
    """
    
    # --- 1. Skill Self-Ratings (Target Max: 40) ---
    # Formula given:
    # Programming * 2
    # DSA * 2
    # ML_AI * 1.6
    # Web_Dev * 1.2
    # Tools * 1.2
    # Note: If inputs are 1-10, max raw score is 80.
    # We will apply min(score, 40) to respect the section weight.
    
    prog = float(self_ratings.get("Programming", 0))
    dsa = float(self_ratings.get("DSA", 0))
    ml = float(self_ratings.get("ML_AI", 0))
    web = float(self_ratings.get("Web_Dev", 0))
    tools = float(self_ratings.get("Tools", 0))
    
    raw_skills_score = (
        (prog * 2) + 
        (dsa * 2) + 
        (ml * 1.6) + 
        (web * 1.2) + 
        (tools * 1.2)
    )
    
    # Cap skills score at 40
    skills_score = min(raw_skills_score, 40.0)


    # --- 2. Resume Score (Target Max: 30) ---
    # Formula:
    # min(len(skills), 10) * 1.5  -> Max 15 points
    # +10 if education exists
    # +5 if experience exists
    
    skills_list = resume_data.get("skills", [])
    education_list = resume_data.get("education", [])
    experience_list = resume_data.get("experience", [])
    
    # Skill count score
    skill_count = len(skills_list)
    resume_skills_score = min(skill_count, 10) * 1.5
    
    # Education score
    resume_edu_score = 10 if len(education_list) > 0 else 0
    
    # Experience score
    resume_exp_score = 5 if len(experience_list) > 0 else 0
    
    resume_score = resume_skills_score + resume_edu_score + resume_exp_score
    resume_score = min(resume_score, 30.0) # Safety cap


    # --- 3. GitHub Score (Target Max: 30) ---
    # Formula:
    # min(public_repos, 20) * 0.5 -> Max 10 points
    # min(total_stars, 50) * 0.2  -> Max 10 points
    # +10 if last_activity within 6 months
    
    public_repos = int(github_data.get("public_repos", 0))
    total_stars = int(github_data.get("total_stars", 0))
    last_activity_str = github_data.get("last_activity") # Expected format YYYY-MM-DD or None
    
    # Repos score
    gh_repo_score = min(public_repos, 20) * 0.5
    
    # Stars score
    gh_stars_score = min(total_stars, 50) * 0.2
    
    # Activity score
    gh_activity_score = 0
    if last_activity_str:
        try:
            # Flexible date parsing
            # Assuming format could be "YYYY-MM-DD" or similar ISO
            last_activity_date = datetime.strptime(str(last_activity_str)[:10], "%Y-%m-%d")
            
            # Check if within 6 months (approx 180 days)
            delta = datetime.now() - last_activity_date
            if delta.days <= 180:
                gh_activity_score = 10
        except (ValueError, TypeError):
             # Make checking safe for invalid formats like "N/A"
             pass
             
    github_score = gh_repo_score + gh_stars_score + gh_activity_score
    github_score = min(github_score, 30.0) # Safety cap


    # --- Final Calculation ---
    overall_score = skills_score + resume_score + github_score
    overall_score = min(overall_score, 100.0)
    
    return {
        "overall_score": int(round(overall_score)),
        "breakdown": {
            "skills": int(round(skills_score)),
            "resume": int(round(resume_score)),
            "github": int(round(github_score))
        }
    }
