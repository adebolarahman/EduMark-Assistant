from typing import Dict, Any
from .base_agent import BaseAgent
from datetime import datetime


class RecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="EduMark Recommender",
            instructions="""Generate final recommendations for the student based on:
            1. Extracted submission insights
            2. Performance analysis (strengths and weaknesses)
            3. Areas for improvement
            Provide clear, actionable next steps, tailored study recommendations, and specific learning resources where applicable.""",
        )

    async def run(self, messages: list) -> Dict[str, Any]:
        """Generate final recommendations for the student"""
        print("💡 EduMark Recommender: Generating final recommendations")

        # Parse the workflow context from the previous stages
        try:
            workflow_context = eval(messages[-1]["content"])
        except Exception as e:
            print(f"Error parsing workflow context: {e}")
            return {
                "final_recommendation": "Error: Unable to process recommendations.",
                "recommendation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "confidence_level": "low",
            }

        # Extract performance data
        strengths = workflow_context.get("strengths", [])
        weaknesses = workflow_context.get("weaknesses", [])
        topics_covered = workflow_context.get("topics_covered", [])
        feedback = workflow_context.get("feedback", {})

        # Generate tailored recommendations
        recommendations = {
            "next_steps": (
                f"Focus on improving {', '.join(weaknesses)} through targeted practice and review. "
                f"Consider revisiting the following topics: {', '.join(topics_covered[:3])}."
            ),
            "resources": [
                {"topic": topic, "resource": f"Recommended resource for {topic}."}
                for topic in weaknesses
            ],
            "encouragement": (
                f"Great work on {', '.join(strengths)}! Keep building on these skills to maintain your strong performance."
            ),
        }

        # Generate timestamp dynamically
        recommendation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "final_recommendation": recommendations,
            "recommendation_timestamp": recommendation_timestamp,
            "confidence_level": "high",
        }
