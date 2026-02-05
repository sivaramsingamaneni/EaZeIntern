import sqlite3
import os

DB_NAME = "internship.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # check_same_thread=False is required for SQLite to work with FastAPI's 
    # multi-threaded/async environment. It allows a connection created in one thread 
    # to be used in another, preventing ProgrammingError.
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the applicants table if it doesn't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
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
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def create_applicant(conn, data):
    """
    Inserts a new applicant into the database.
    data format:
    (full_name, email, college, degree, github, kaggle_url, resume_path, parsed_resume_json, github_json, self_rating_json, application_id, overall_score, score_breakdown_json)
    
    Uses the provided connection 'conn' to execute the insert.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applicants 
        (full_name, email, college, degree, github, kaggle_url, resume_path, parsed_resume_json, github_json, self_rating_json, application_id, overall_score, score_breakdown_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()

def get_db():
    """
    Dependency that provides a new database session per request.
    Yields the connection and closes it after the request is processed.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Auto-initialize for convenience, though in prod this might be explicit
if __name__ == "__main__":
    init_db()
    print(f"Database {DB_NAME} initialized.")
