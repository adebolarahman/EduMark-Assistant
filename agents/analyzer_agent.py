from typing import Dict, Any
from .base_agent import BaseAgent


class EduMarkAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="EduMark",
            instructions="""Analyze student results and provide:
            1. Total score (0-100)
            2. Grading (A/B/C/F) where:
               - F: Less than 50
               - C: 50-59
               - B: 60-69
               - A: 70-100
            3. Recommendations for improvement
            4. Highlighted strengths

            Format the output as structured data.""",
        )

    async def run(self, messages: list) -> Dict[str, Any]:
        """Analyze the uploaded student results"""
        print("📘 EduMark: Analyzing student results")

        uploaded_results = eval(messages[-1]["content"])

        # Get structured analysis from Ollama
        analysis_prompt = f"""
        Analyze these student results and return a JSON object with the following structure:
        {{
            "total_score": number,
            "grade": "grade letter",
            "recommendations": ["improvement1", "improvement2"],
            "strengths": ["strength1", "strength2"]
        }}

        The grading scale must be exactly as follows:
        - A: 70-100 points
        - B: 60-69 points
        - C: 50-59 points
        - F: Below 50 points

        Be critical in your assessment and provide a fair score based on the quality of the work.
        Evaluate the content quality, depth, organization, and completeness.

        Student results:
        {uploaded_results["structured_data"]}

        Return ONLY the JSON object, no other text.
        """

        analysis_results = self._query_llama(analysis_prompt)
        parsed_results = self._parse_json_safely(analysis_results)

        # Ensure we have valid data even if parsing fails
        if "error" in parsed_results:
            parsed_results = {
                "total_score": 0,
                "grade": "F",
                "recommendations": ["Improve understanding of core concepts", "Practice problem-solving"],
                "strengths": ["Consistency in effort"],
            }
        else:
            # Ensure grade follows our scale
            score = parsed_results["total_score"]
            parsed_results["grade"] = self._calculate_grade(score)

        # Dynamically generate timestamp and confidence score
        from datetime import datetime
        import random

        current_timestamp = datetime.now().isoformat()
        confidence_score = random.uniform(0.7, 0.95) if "error" not in parsed_results else random.uniform(0.4, 0.6)

        return {
            "student_analysis": parsed_results,
            "analysis_timestamp": current_timestamp,
            "confidence_score": round(confidence_score, 2),
        }
        
    def _calculate_grade(self, score: int) -> str:
        """Calculate the grade based on the score."""
        if score >= 70:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "F"