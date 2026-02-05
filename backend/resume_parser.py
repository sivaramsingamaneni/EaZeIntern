from typing import Dict, Any, List
import pypdf
import re

async def parse_resume(path: str) -> Dict[str, Any]:
    """
    Parses a PDF resume and extracts structured data using rule-based logic.
    Returns a dictionary with name, email, skills, education, and experience.
    """
    full_text = ""
    try:
        # 1. Extract full text from PDF using pypdf
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            extract = page.extract_text()
            if extract:
                full_text += extract + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        # Safe fallback structure
        return {
            "name": "Unknown",
            "email": "Not found",
            "skills": [],
            "education": [],
            "experience": []
        }

    # Split text into lines for line-by-line analysis
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]

    # 2. Extract Name
    # Strategy: First reasonable line that is NOT a section header or contact info
    name = "Unknown"
    
    # Common headers to ignore when looking for a name (uppercase check)
    ignore_headers = {
        "RESUME", "CURRICULUM VITAE", "CV", "BIO", "PROFILE", "SUMMARY", 
        "OBJECTIVE", "SKILLS", "EDUCATION", "EXPERIENCE", "WORK HISTORY", 
        "PROJECTS", "CONTACT", "CONTACT INFO", "DECLARATION", "CERTIFICATIONS",
        "LANGUAGES", "HOBBIES", "ACHIEVEMENTS"
    }
    
    for line in lines:
        # Simplify line logic for check
        # Remove non-alpha for header check
        clean_header_check = re.sub(r'[^a-zA-Z\s]', '', line).upper().strip()
        
        # Skip if it's a known header
        if clean_header_check in ignore_headers:
            continue
            
        # Skip if it looks like an email or phone (simple heuristics)
        if "@" in line or re.search(r'\d{10}', line):
            continue
            
        # Heuristic: A name is usually short (e.g. 2-4 words) and often at the start
        # If it passes these negative checks, we assume it's the name.
        if 0 < len(line.split()) <= 4:
            name = line
            break

    # 3. Extract Email
    # Strategy: Regex for email pattern
    email = "Not found"
    # Basic email regex
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
    if email_match:
        email = email_match.group(0)

    # 4. Extract Skills
    # Strategy: detect from a predefined skills list in the full text (case-insensitive)
    found_skills = set()
    # Extensive list of tech skills
    skills_db = [
        "Python", "Java", "C++", "C", "C#", "JavaScript", "TypeScript", "HTML", "CSS", 
        "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Oracle",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "GitLab",
        "Machine Learning", "Deep Learning", "AI", "Data Science", "Pandas", "NumPy",
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "NLP", "OpenCV",
        "Linux", "Bash", "Shell", "DevOps", "Agile", "Scrum", "Jira"
    ]
    
    lower_text = full_text.lower()
    for skill in skills_db:
        # Use word boundary regex to avoid partial matches (e.g., 'Java' inside 'JavaScript' if not careful, 
        # though 'JavaScript' is in list, 'C' is dangerous without boundaries)
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, lower_text):
            found_skills.add(skill)

    # 5. Extract Education
    # Strategy: detect lines containing education keywords
    education_entries = []
    edu_keywords = ["B.Tech", "M.Tech", "Bachelor", "Master", "PhD", "B.Sc", "M.Sc", "University", "College", "Institute", "Degree"]
    
    for line in lines:
        if any(kw.lower() in line.lower() for kw in edu_keywords):
            # Limit length to avoid capturing long narrative paragraphs unless it's a short description
            if len(line.split()) < 20: 
                education_entries.append(line)

    # 6. Extract Experience / Projects
    # Strategy: detect lines containing keywords like Internship, Experience, Project
    experience_entries = []
    # Broad keywords to catch job titles or section lines. 
    # Note: This is a simple extractor and might catch headers or generic lines.
    exp_keywords = ["Intern", "Internship", "Experience", "Work", "Project", "Developer", "Engineer", "Analyst", "Associate", "Consultant"]
    
    for line in lines:
        if any(kw.lower() in line.lower() for kw in exp_keywords):
            # Heuristic: Avoid very long lines that might be descriptions
            if len(line.split()) < 15:
                experience_entries.append(line)

    return {
        "name": name,
        "email": email,
        "skills": list(found_skills),
        "education": education_entries,
        "experience": experience_entries
    }
