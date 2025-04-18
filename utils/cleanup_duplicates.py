import sqlite3
import sys
import os
from pathlib import Path

# Adjust this path to point to your project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import EduMarkDatabase

def cleanup_duplicates():
    """Clean up duplicate student IDs, keeping only the most recent submission."""
    print("Starting database cleanup...")
    
    try:
        # Get database path
        db = EduMarkDatabase()
        db_path = db.db_path
        print(f"Database path: {db_path}")
        
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Find all unique student IDs that have duplicates
            cursor.execute("""
                SELECT student_id, COUNT(*) as count
                FROM submissions
                GROUP BY student_id
                HAVING count > 1
            """)
            
            duplicates = cursor.fetchall()
            
            if not duplicates:
                print("No duplicate student IDs found. Database is clean.")
                return
            
            print(f"Found {len(duplicates)} student IDs with duplicate records.")
            
            # For each duplicate set, keep only the most recent one
            for student_id, count in duplicates:
                print(f"Processing student ID: {student_id} with {count} duplicates")
                
                # Find all records for this student ID, ordered by created_at (most recent first)
                cursor.execute("""
                    SELECT id, created_at
                    FROM submissions
                    WHERE student_id = ?
                    ORDER BY created_at DESC
                """, (student_id,))
                
                records = cursor.fetchall()
                
                # Keep the most recent record and delete others
                most_recent_id = records[0][0]  # First record is most recent due to DESC order
                
                # Delete all records except the most recent one
                cursor.execute("""
                    DELETE FROM submissions
                    WHERE student_id = ? AND id != ?
                """, (student_id, most_recent_id))
                
                deleted_count = cursor.rowcount
                print(f"  Kept record {most_recent_id} and deleted {deleted_count} older records")
            
            conn.commit()
            print("Cleanup completed successfully!")
            
            # Report final count of records
            cursor.execute("SELECT COUNT(*) FROM submissions")
            total_records = cursor.fetchone()[0]
            print(f"Total records in database after cleanup: {total_records}")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_duplicates()