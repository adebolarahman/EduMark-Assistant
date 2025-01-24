import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import json
import os


class EduMarkDatabase:
    def __init__(self):
        # Get the directory where the script is located
        current_dir = Path(__file__).parent
        self.db_path = current_dir / "edumark.sqlite"
        self.schema_path = current_dir / "schema.sql"
        self._init_db()

    def _init_db(self):
        """Initialize the database with the provided schema."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {self.schema_path}")

        with open(self.schema_path) as f:
            schema = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def add_submission(self, submission_data: Dict[str, Any]) -> int:
        """
        Add a new student submission to the database.
        """
        query = """
        INSERT INTO submissions (
            student_name, student_id, submission_text, 
            topics_covered, strengths, weaknesses, feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    submission_data["student_name"],
                    submission_data["student_id"],
                    submission_data["submission_text"],
                    json.dumps(submission_data["topics_covered"]),
                    json.dumps(submission_data["strengths"]),
                    json.dumps(submission_data["weaknesses"]),
                    submission_data.get("feedback", ""),
                ),
            )
            return cursor.lastrowid

    def get_all_submissions(self) -> List[Dict[str, Any]]:
        """
        Retrieve all student submissions from the database.
        """
        query = "SELECT * FROM submissions ORDER BY created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "student_name": row["student_name"],
                    "student_id": row["student_id"],
                    "submission_text": row["submission_text"],
                    "topics_covered": json.loads(row["topics_covered"]),
                    "strengths": json.loads(row["strengths"]),
                    "weaknesses": json.loads(row["weaknesses"]),
                    "feedback": row["feedback"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def search_submissions(
        self, topics: List[str], strengths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search submissions based on topics and strengths.
        """
        query = """
        SELECT * FROM submissions
        WHERE (
        """
        query_conditions = []
        params = []

        # Add LIKE conditions for topics
        for topic in topics:
            query_conditions.append("topics_covered LIKE ?")
            params.append(f"%{topic}%")

        # Add LIKE conditions for strengths
        for strength in strengths:
            query_conditions.append("strengths LIKE ?")
            params.append(f"%{strength}%")

        query += " OR ".join(query_conditions) + ")"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    {
                        "id": row["id"],
                        "student_name": row["student_name"],
                        "student_id": row["student_id"],
                        "submission_text": row["submission_text"],
                        "topics_covered": json.loads(row["topics_covered"]),
                        "strengths": json.loads(row["strengths"]),
                        "weaknesses": json.loads(row["weaknesses"]),
                        "feedback": row["feedback"],
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error searching submissions: {e}")
            return []

    def add_feedback(self, submission_id: int, feedback: str) -> bool:
        """
        Add or update feedback for a specific student submission.
        """
        query = """
        UPDATE submissions
        SET feedback = ?
        WHERE id = ?
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (feedback, submission_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating feedback: {e}")
            return False
