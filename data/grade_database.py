import json
from typing import Dict, Any
from groq import Groq
from crewai import Agent, LLM
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq and LLM client
llama_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
llm = LLM(model="groq/llama-3.1-70b-versatile")

# Extractor agent: Extracts relevant information from student submissions
def extractor_agent_function(submission: str) -> Dict[str, Any]:
    """
    Extracts key details such as student name, strengths, weaknesses, topics covered, 
    and any other relevant grading data from the submitted document.
    """
    try:
        # Query Groq for structured extraction
        response = llama_client.chat.completions.create(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract the following details from the student's submission:\n"
                        "- Student name\n"
                        "- Strengths (areas where the student performed well)\n"
                        "- Weaknesses (areas needing improvement)\n"
                        "- Topics covered in the submission\n"
                        "- Any specific feedback or red flags\n\n"
                        "Provide the extracted data in valid JSON format."
                    ),
                },
                {"role": "user", "content": submission},
            ],
        )
        
        # Parse the LLM response
        extracted_data = json.loads(response["completion"].strip())
        return extracted_data

    except Exception as e:
        print(f"Error in extracting data: {e}")
        return {"error": str(e)}

# Initialize the Extractor Agent
extractor_agent = Agent(
    name="EduMark Extractor Agent",
    llm=llm,
    instructions="Extract key details such as strengths, weaknesses, and topics covered from student submissions.",
    functions=[extractor_agent_function],
)
