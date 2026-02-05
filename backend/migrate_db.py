import sqlite3
import os

DB_NAME = "internship.db"

def migrate():
    if not os.path.exists(DB_NAME):
        print("Database not found, nothing to migrate.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "overall_score" not in columns:
            print("Adding overall_score to applicants table...")
            cursor.execute("ALTER TABLE applicants ADD COLUMN overall_score REAL")
            
        if "score_breakdown_json" not in columns:
            print("Adding score_breakdown_json to applicants table...")
            cursor.execute("ALTER TABLE applicants ADD COLUMN score_breakdown_json TEXT")
            
        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
