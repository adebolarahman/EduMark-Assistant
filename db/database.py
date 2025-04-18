import sqlite3
from pathlib import Path
from typing import Dict, List, Any
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EduMarkDatabase:
    def __init__(self):
        self.db_path = Path("edumark.sqlite")
        self._init_db()

    def _init_db(self):
        """Initialize the database with baseline data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT,
                    student_id TEXT,
                    submission_text TEXT,
                    topics_covered TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    feedback TEXT,
                    score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS baseline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference_text TEXT
                )
            """
            )
            
            # Insert baseline data if not already added
            cursor.execute("SELECT COUNT(*) FROM baseline")
            if cursor.fetchone()[0] == 0:
                baseline_docs = [
                    "This is a reference essay on climate change.",
                    "A detailed analysis of machine learning techniques.",
                    "A well-structured business strategy for startups."
                ]
                cursor.executemany("INSERT INTO baseline (reference_text) VALUES (?)", [(doc,) for doc in baseline_docs])

    def add_submission(self, student_name, student_id, submission_text):
        """Add a new submission and compute its similarity score."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reference_text FROM baseline")
            baseline_texts = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT submission_text FROM submissions")
            past_submissions = [row[0] for row in cursor.fetchall()]

            all_texts = baseline_texts + past_submissions + [submission_text]
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(all_texts)

            similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            max_similarity = max(similarity_scores) if similarity_scores.size > 0 else 0
            score = max(100 - int(max_similarity * 100), 10)  # Ensures min score of 10
            
            cursor.execute(
                """INSERT INTO submissions (student_name, student_id, submission_text, score) 
                    VALUES (?, ?, ?, ?)""",
                (student_name, student_id, submission_text, score)
            )
            return score

    def get_all_submissions(self):
        """Retrieve all student submissions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

# Usage example
if __name__ == "__main__":
    db = EduMarkDatabase()
    new_score = db.add_submission("John Doe", "12345", "This is a test submission about business strategy.")
    print(f"New submission scored: {new_score}/100")
    print("All Submissions:", db.get_all_submissions())