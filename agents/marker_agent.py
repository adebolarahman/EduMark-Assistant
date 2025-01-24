from typing import Dict, Any
from .base_agent import BaseAgent
from datetime import datetime


class ScreenerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Marker",
            instructions="""Mark students' solution paper based on:
            - Marking guide
            - Alignment with the answer providers
            - Clarity of the document
            - Closest similarity with the answer sheet
            - Red flags or concerns (e.g., plagiarism)
            Provide a comprehensive result report in JSON format with strengths, weaknesses, and grading details.""",
        )

    def _calculate_score(self, workflow_context: dict) -> int:
        """Calculate the student score based on the workflow context."""
        similarity = workflow_context.get("similarity", 0)
        clarity = workflow_context.get("clarity", 0)
        alignment = workflow_context.get("alignment", 0)
        red_flags = workflow_context.get("red_flags", 0)

        # Weighted scoring logic
        score = (
            (similarity * 0.4)
            + (clarity * 0.3)
            + (alignment * 0.25)
            - (red_flags * 0.05)
        )
        return max(0, min(int(score * 100), 100))  # Ensure the score is between 0-100

    async def run(self, messages: list) -> Dict[str, Any]:
        """Mark the student's solution paper."""
        print("👥 Marker: Conducting initial marking")

        try:
            # Extract the workflow context from the last message
            workflow_context = eval(messages[-1]["content"])
        except Exception as e:
            print(f"Error parsing workflow context: {e}")
            return {
                "marking_report": "Error processing workflow context.",
                "marking_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "student_score": 0,
            }

        # Query Llama for detailed marking
        marking_prompt = f"""
        Mark the student paper based on the following context:
        {workflow_context}

        Provide a JSON report structured as:
        {{
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "grading_details": {{
                "introduction": "score/10",
                "content": "score/10",
                "references": "score/10",
                "citation": "score/10",
                "data_usage": "score/10",
                "tables": "score/10",
                "images": "score/10",
                "recommendation": "score/10",
                "summary": "score/10"
            }}
        }}
        """
        marking_results = self._query_llama(marking_prompt)

        # Dynamically calculate the score
        student_score = self._calculate_score(workflow_context)

        return {
            "marking_report": marking_results,
            "marking_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "student_score": student_score,
        }
