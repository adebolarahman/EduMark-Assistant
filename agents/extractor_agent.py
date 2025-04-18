from typing import Dict, Any
from pdfminer.high_level import extract_text 
from .base_agent import BaseAgent

class ExtractorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Extractor",
            instructions="""Extract and structure information from student solution sheets.
            Focus on: Introduction, content, references, citations, data, tables, images, recommendations, and summary.
            Provide output in a clear, structured format."""
        )
    
    async def run(self, messages: list) -> Dict[str, Any]:
        """Process the student solution sheet and extract information"""
        print("📄 Extractor: Processing student solution sheet")
        
        report_data = eval(messages[-1]["content"])
        
        # Extract text from PDF
        if report_data.get("file_path"):
            raw_text = extract_text(report_data["file_path"])
        else:
            raw_text = report_data.get("text", "")

        # Get structured information from EduMark
        extraction_prompt = f"""
        Analyze the following extracted text from a student solution sheet and structure it into a JSON object with the following fields:
        {{
            "introduction": "",
            "content": "",
            "references": "",
            "citations": "",
            "data": "",
            "tables": "",
            "images": "",
            "recommendations": "",
            "summary": ""
        }}

        Extracted text:
        {raw_text}

        Return ONLY the JSON object, no other text.
        """

        extracted_info = self._query_llama(extraction_prompt)
        parsed_info = self._parse_json_safely(extracted_info)

        # Ensure valid data even if parsing fails
        if "error" in parsed_info:
            parsed_info = {
                "introduction": "Not found",
                "content": "Not found",
                "references": "Not found",
                "citations": "Not found",
                "data": "Not found",
                "tables": "Not found",
                "images": "Not found",
                "recommendations": "Not found",
                "summary": "Not found",
            }

        return {
            "raw_text": raw_text,
            "structured_data": parsed_info,
            "extraction_status": "completed"
        }