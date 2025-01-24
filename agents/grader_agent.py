from typing import Dict, Any, List
from .base_agent import BaseAgent
from db.database import EduMarkDatabase
import json
import ast
import re
import sqlite3
from datetime import datetime


class GraderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Grader",
            instructions="""Grade student results with grade bands.
            Consider: Introduction, content, references, citations, data, tables, images, recommendations, and summary.
            Provide detailed reasoning and compatibility scores.
            Return grades in JSON format with grade, score, and location fields.""",
        )
        self.db = EduMarkDatabase()

    async def run(self, messages: list) -> Dict[str, Any]:
        """Grade student results based on available criteria"""
        print("🎯 Grader: Grading student results")

        try:
            # Convert single quotes to double quotes to make it valid JSON
            content = messages[-1].get("content", "{}").replace("'", '"')
            analysis_results = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error parsing analysis results: {e}")
            return {
                "graded_results": [],
                "grade_timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "number_of_grades": 0,
            }

        # Extract content and important data for grading
        result_analysis = analysis_results.get("result_analysis", {})
        if not result_analysis:
            print("No result analysis provided in the input.")
            return {
                "graded_results": [],
                "grade_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "number_of_grades": 0,
            }

        # Extract contents and grade band directly
        contents = result_analysis.get("contents", [])
        grade_band = result_analysis.get("grade_band", "Pass")

        if not isinstance(contents, list) or not contents:
            print("No valid contents found, defaulting to an empty list.")
            contents = []

        if grade_band not in ["Fail", "Pass", "Merit", "Distinction"]:
            print("Invalid grade band detected, defaulting to Pass.")
            grade_band = "Pass"

        print(f" ==>>> Contents: {contents}, Grade Band: {grade_band}")
        # Search grades database
        matching_grades = self.search_grades(contents, grade_band)

        # Calculate match scores
        scored_grades = []
        for grade in matching_grades:
            # Calculate match score based on requirements overlap
            required_grades = set(grade["requirements"])
            candidate_grades = set(contents)
            overlap = len(required_grades.intersection(candidate_grades))
            total_required = len(required_grades)
            match_score = (
                int((overlap / total_required) * 100) if total_required > 0 else 0
            )

            # Lower threshold for matching to 30%
            if match_score >= 30:  # Include grades with >30% match
                scored_grades.append(
                    {
                        "title": grade['title'],
                        "match_score": f"{match_score}%",
                        "location": grade["location"],
                        "grade_band": grade["grade_band"],
                        "requirements": grade["requirements"],
                    }
                )

        print(f" ==>>> Scored Grades: {scored_grades}")
        # Sort by match score
        scored_grades.sort(key=lambda x: int(x["match_score"].rstrip("%")), reverse=True)

        return {
            "graded_results": scored_grades[:3],  # Top 3 grades
            "grade_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "number_of_grades": len(scored_grades),
        }

    def search_grades(
        self, contents: List[str], grade_band: str
    ) -> List[Dict[str, Any]]:
        """Search grades based on contents and grade level"""
        query = """
        SELECT * FROM grades
        WHERE grade_band = ?
        AND (
        """
        query_conditions = []
        params = [grade_band]

        # Create LIKE conditions for each content
        for content in contents:
            query_conditions.append("requirements LIKE ?")
            params.append(f"%{content}%")

        query += " OR ".join(query_conditions) + ")"

        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "location": row["location"],
                        "grade_band": row["grade_band"],
                        "requirements": json.loads(row["requirements"]),
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error searching grades: {e}")
            return []
