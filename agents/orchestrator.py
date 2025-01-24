from typing import Dict, Any
from .base_agent import BaseAgent
from .extractor_agent import ExtractorAgent
from .analyzer_agent import EduMarkAgent
from .grader_agent import GraderAgent
from .marker_agent import ScreenerAgent
from .recommender_agent import RecommenderAgent


class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            instructions="""Coordinate the grading workflow and delegate tasks to specialized agents.
            Ensure proper flow of information between extraction, analysis, grading, marking, and recommendation phases.
            Maintain context and aggregate results from each stage.""",
        )
        self._setup_agents()

    def _setup_agents(self):
        """Initialize all specialized agents"""
        self.extractor = ExtractorAgent()
        self.analyzer = EduMarkAgent()
        self.matcher = GraderAgent()
        self.screener = ScreenerAgent()
        self.recommender = RecommenderAgent()

    async def run(self, messages: list) -> Dict[str, Any]:
        """Process a single message through the orchestrator"""
        prompt = messages[-1]["content"]
        response = self._query_llama(prompt)
        return self._parse_json_safely(response)

    async def process_student_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main workflow orchestrator for processing student submissions"""
        print("🎯 Orchestrator: Starting grading workflow")

        workflow_context = {
            "submission_data": submission_data,
            "status": "initiated",
            "current_stage": "extraction",
        }

        try:
            # Step 1: Extract relevant information from the submission
            extracted_data = await self.extractor.run(
                [{"role": "user", "content": str(submission_data)}]
            )
            workflow_context.update(
                {"extracted_data": extracted_data, "current_stage": "analysis"}
            )

            # Step 2: Analyze the extracted data
            analysis_results = await self.analyzer.run(
                [{"role": "user", "content": str(extracted_data)}]
            )
            workflow_context.update(
                {"analysis_results": analysis_results, "current_stage": "grading"}
            )

            # Step 3: Grade the submission based on predefined bands
            grading_results = await self.matcher.run(
                [{"role": "user", "content": str(analysis_results)}]
            )
            workflow_context.update(
                {"grading_results": grading_results, "current_stage": "marking"}
            )

            # Step 4: Mark the submission with detailed feedback
            marking_results = await self.screener.run(
                [{"role": "user", "content": str(workflow_context)}]
            )
            workflow_context.update(
                {
                    "marking_results": marking_results,
                    "current_stage": "recommendation",
                }
            )

            # Step 5: Provide tailored recommendations based on the marking results
            final_recommendation = await self.recommender.run(
                [{"role": "user", "content": str(workflow_context)}]
            )
            workflow_context.update(
                {"final_recommendation": final_recommendation, "status": "completed"}
            )

            return workflow_context

        except Exception as e:
            workflow_context.update({"status": "failed", "error": str(e)})
            print(f"🚨 Error during workflow: {e}")
            raise
