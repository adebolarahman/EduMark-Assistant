from typing import Dict, Any
from groq import Agent


# Submission Enhancer Agent: Enhances the student's submission analysis
def submission_enhancer_agent_function(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    enhanced_analysis = extracted_info.copy()

    # Calculate total strengths and weaknesses
    strengths = extracted_info.get("strengths", [])
    weaknesses = extracted_info.get("weaknesses", [])
    topics_covered = extracted_info.get("topics_covered", [])
    
    # Generate a summary for the student
    enhanced_analysis["summary"] = (
        f"The student demonstrated strengths in {', '.join(strengths)}, "
        f"but should focus on improving {', '.join(weaknesses)}. "
        f"The submission covered {len(topics_covered)} key topics, including {', '.join(topics_covered[:3])}."
    )

    # Provide tailored feedback
    enhanced_analysis["feedback"] = {
        "strengths_feedback": f"Great job on {', '.join(strengths)}! Keep up the excellent work in these areas.",
        "weaknesses_feedback": f"Consider reviewing the following topics for improvement: {', '.join(weaknesses)}.",
    }

    return enhanced_analysis


submission_enhancer_agent = Agent(
    name="Submission Enhancer Agent",
    model="llama3.2",
    instructions="Enhance the analysis of the student's submission based on the extracted information, identifying strengths, weaknesses, and key areas for improvement.",
    functions=[submission_enhancer_agent_function],
)
