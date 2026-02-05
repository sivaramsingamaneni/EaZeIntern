# EazeIntern

EazeIntern is a smart internship application intake system designed to streamline the recruitment process. It automates application submission, resume parsing, candidate scoring, and recruiter workflows, replacing scattered email submissions with a centralized, data-driven dashboard.

## Problem Statement

Traditional internship recruitment suffers from manual data entry, scattered resumes across emails, and subjective initial screening. Recruiters often spend excessive time filtering unqualified candidates rather than focusing on top talent. EazeIntern addresses this by automating data extraction and providing instant, quantified insights into every applicant.

## Key Features

### For Applicants
- **Seamless Application Portal**: A clean, single-page application form.
- **Auto-Tracking**: Real-time application status tracking using a unique ID.
- **Email Confirmation**: Automated confirmation emails upon successful submission.

### For Recruiters
- **Centralized Dashboard**: View all applicants in a sortable, filterable list.
- **Automated Resume Parsing**: Extracts skills, education, and experience from PDFs.
- **GitHub Enrichment**: Fetches and analyzes public GitHub profiles (repos, stars, languages).
- **Smart Scoring**: an algorithm calculates an "Overall Score" based on self-ratings, resume keywords, and GitHub activity.
- **Search & Filter**: Real-time keyword search for names, colleges, degrees, and skills.
- **Hover Insights**: Instant summary of candidate stats on hover (macOS-style inspector).
- **Data Export**: Export candidate data to CSV (filtered view) or JSON (full database dump).

## System Architecture

The system follows a modern client-server architecture:

1.  **Frontend**: HTML5/CSS3 templates served by FastAPI (server-side rendering).
2.  **Backend**: FastAPI (Python) handles API endpoints, business logic, and background tasks.
3.  **Database**: SQLite for lightweight, reliable persistent storage.
4.  **File Storage**: Local file system storage for PDF resumes.
5.  **External Integrations**: GitHub API for profile analysis.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Database**: SQLite
- **Frontend**: HTML5, Vanilla CSS (Apple-inspired design system), JavaScript
- **Libraries**: `pypdf` (resume parsing), `httpx` (async API calls), `jinja2` (templating)

## Project Structure

```
internship_app/
├── applications/        # Stores applicant resumes and profile data
├── backend/             # Implement FastAPI backend, business logic, integrations, and data handling
│   ├── database.py      # DB connection and models
│   ├── main.py          # Application entry point and routes
│   ├── email_service.py # Email notification logic
│   ├── github_service.py# GitHub API integration
│   ├── resume_parser.py # PDF extraction logic
│   ├── scoring.py       # Candidate ranking algorithm
│   └── utils.py         # Helper functions
├── static/              # Store frontend static assets including CSS, animations, and branding
├── templates/           # Define Jinja2 HTML templates for user and admin interfaces
├── tests/               # Add automated pytest test cases covering positive, negative, and edge scenarios
├── .gitignore           # Exclude environment files, virtual environments, and build artifacts
├── Dockerfile           # Containerize the application for consistent runtime and test execution
├── docker-compose.yml   # Configure multi-container setup for application and test orchestration
├── requirements.txt     # Specify Python dependencies required to run the application and tests
├── README.md            # Document project overview, setup, Docker usage, and testing strategy
├── .env                 # Environment variables
└── internship.db        # SQLite database file
```

## Setup & Run Instructions

### 1. Prerequisites
- Python 3.10 or higher installed.
- Git installed.

### 2. Installation

Clone the repository and navigate to the project folder:
```bash
git clone <repository_url>
cd internship_app
```

Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Application Security
SECRET_KEY=your_secure_random_key

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword

# Email Configuration (Gmail App Password)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 4. Running the Server

Start the application using Uvicorn:
```bash
python backend/main.py
```

Access the application at: `http://127.0.0.1:8000`

## Authentication Design

- **Applicant Access**: Public access for `apply` and `track` routes to lower entry barriers.
- **Admin Access**: Protected via session-based authentication using `ADMIN_USERNAME` and `ADMIN_PASSWORD` stored in environment variables. Middleware ensures secure access to dashboard and export endpoints.

## Candidate Scoring Overview

The scoring engine evaluates candidates out of 100 points based on:
1.  **Self-Reported Skills (30%)**: Weighted average of technical proficiency.
2.  **Resume Analysis (40%)**: Keyword matching against a known tech stack database.
3.  **GitHub Activity (30%)**: Analysis of public repositories, stars, and language diversity.

## Export & Search Capabilities

- **Search**: A client-side real-time filter allows searching by name, skill, college, or degree.
- **Export CSV**: Downloads the currently visible (filtered) list of candidates with key summary fields.
- **Export JSON**: Downloads the full database dump of all candidates, including deep nested structures (parsed resume data, score breakdown) for backup or external analysis.

## Testing & Validation

The application ecosystem is verified through a comprehensive suite of automated tests using `pytest`. The test suite covers 9 distinct scenarios across three categories:

1.  **Positive Test Cases**: Validates the happy path for application submission, parsing, admin authentication, tracking, and data exports.
2.  **Negative Test Cases**: Ensures graceful handling of invalid file types, missing fields, incorrect credentials, and bad API responses.
3.  **Edge Cases**: Tests system stability under boundary conditions (e.g., empty resumes, zero-repo GitHub profiles, rapid UI interactions).

### Running Tests Inside Docker

For a consistent and isolated testing environment, the entire test suite is containerized.

**Build the image:**
```bash
docker build -t eazeintern .
```

**Run the tests:**
```bash
docker run -it eazeintern pytest
```

*All tests are currently passing in the containerized environment.*

## What Is Working

- **Full Application Lifecycle**: Submission form → Email confirmation → Status tracking → Admin review.
- **Automated Intelligence**: PDF resume parsing for key skills/education and GitHub profile analysis for technical validation.
- **Dashboards**: 
    - **Candidate**: Real-time status updates.
    - **Admin**: Searchable, filterable list with "macOS-style" hover previews.
- **Data Management**: Secure SQLite storage with capabilities to bulk export data to CSV (filtered view) or JSON (full backup).
- **DevOps**: Fully Dockerized application and test suite for reproducible deployments.

## Known Limitations

- **Resume Parsing**: The module relies on heuristic keyword matching (`pypdf`). While effective for standard formats, it may struggle with image-heavy or complex multi-column layouts.
- **Database**: SQLite is used for simplicity and portability. For high-concurrency production environments, migration to PostgreSQL is recommended.
- **Framework Warnings**: Minor deprecation warnings from underlying libraries (e.g., `pkg_resources` in some environments) may appear in logs but do not impact application functionality.
- **Email Delivery**: The SMTP implementation depends on environment configuration. Fallback logging is implemented to ensure no data is lost if email providers reject connections.

## Future Work

- **AI Integration**: Implementing LLM-based resume analysis for semantic matching (replacing keyword heuristics).
- **Scalable Infrastructure**: Migrating file storage to AWS S3 and database to PostgreSQL.
- **Role-Based Access Control (RBAC)**: Introducing tiered permissions for various recruiter roles.
- **Advanced Analytics**: Visual dashboards for demographic and skill-distribution trends.
- **Production Email**: Integration with SendGrid or AWS SES for reliable transactional emails.

## Closing Note

EazeIntern is designed as a robust, professional-grade prototype. It foundationalizes core recruitment automation while maintaining a high standard of code quality and user experience. The modular architecture ensures it is ready for further scaling and feature integration.
