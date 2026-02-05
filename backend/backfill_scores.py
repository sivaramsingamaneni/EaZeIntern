import sqlite3
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.scoring import calculate_score

DB_NAME = "internship.db"

def backfill_scores():
    if not os.path.exists(DB_NAME):
        print(f"Dataset {DB_NAME} not found!")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Fetch all applicants with NULL overall_score
        cursor.execute("SELECT * FROM applicants WHERE overall_score IS NULL")
        applicants = cursor.fetchall()
        
        print(f"Found {len(applicants)} applicants with missing scores.")

        for app in applicants:
            app_id = app["application_id"]
            
            # Helper to safely load JSON
            def load_json(json_str):
                try:
                    return json.loads(json_str) if json_str else {}
                except json.JSONDecodeError:
                    return {}

            self_ratings = load_json(app["self_rating_json"])
            resume_data = load_json(app["parsed_resume_json"])
            github_data = load_json(app["github_json"])
            
            # Recalculate Score
            score_result = calculate_score(self_ratings, resume_data, github_data)
            overall = score_result.get("overall_score", 0)
            breakdown = score_result.get("breakdown", {})
            
            print(f"Updating {app_id}: Score {overall}")

            # Update DB
            cursor.execute("""
                UPDATE applicants 
                SET overall_score = ?, score_breakdown_json = ?
                WHERE application_id = ?
            """, (overall, json.dumps(breakdown), app_id))
        
        conn.commit()
        print("✅ Backfill Complete.")

        # Verify
        cursor.execute("SELECT count(*) FROM applicants WHERE overall_score IS NULL")
        count = cursor.fetchone()[0]
        print(f"Remaining NULL scores: {count}")

    except Exception as e:
        print(f"Backfill failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    backfill_scores()
