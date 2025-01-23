#from phi.agent import Agent
#from phi.model.groq import Groq
from groq import Groq
from dotenv import load_dotenv  
from typing import Dict, Any
import json
import os
load_dotenv()

class BaseAgent:
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions
        self.llama_client =Groq(api_key=os.getenv("GROQ_API_KEY"))
    async def run(self, messages: list) -> Dict[str, Any]:
        """Default run method to be overridden by child classes"""
        raise NotImplementedError("Subclasses must implement run()")
    def _query_llama(self, prompt: str) -> str:
        """Query llama model with the given prompt"""
        try:
            response = self.llama_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  
                messages=[
                    {"role": "system", "content": self.instructions},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error querying llama: {str(e)}")
            raise
    def _parse_json_safely(self, text: str) -> Dict[str, Any]:

        """Safely parse JSON from text, handling potential errors"""
        try:
            # Try to find JSON-like content between curly braces
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start : end + 1]
                return json.loads(json_str)
            return {"error": "No JSON content found"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON content"}
