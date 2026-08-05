from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class ProblemStatement(BaseModel):
    problem_id: str = Field(..., description="Unique identifier for the problem")
    description: str = Field(..., description="Detailed description of the problem")
    context: Dict[str, Any] = Field({}, description="Relevant context for the problem")
    expected_outcome: Optional[Any] = Field(None, description="Expected outcome if the problem is solved")

class Solution(BaseModel):
    solution_id: str = Field(..., description="Unique identifier for the solution")
    description: str = Field(..., description="Description of the proposed solution")
    steps: List[str] = Field([], description="Steps to execute the solution")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) in the solution")
    reasoning_path: List[str] = Field([], description="Path of reasoning taken to arrive at the solution")

class InferenceResult(BaseModel):
    query: str = Field(..., description="The original query")
    answer: str = Field(..., description="Inferred answer or conclusion")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) in the inference")
    supporting_facts: List[str] = Field([], description="Facts or evidence supporting the inference")

class ReflectionReport(BaseModel):
    task_id: str = Field(..., description="ID of the task being reflected upon")
    outcome_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"] = Field(..., description="Outcome of the task")
    lessons_learned: List[str] = Field([], description="Key lessons learned from the task execution")
    identified_errors: List[str] = Field([], description="Errors or inefficiencies identified")
    suggested_improvements: List[str] = Field([], description="Suggestions for future improvements")

class VerificationResult(BaseModel):
    item_id: str = Field(..., description="ID of the item being verified (e.g., task_id, plan_id)")
    is_valid: bool = Field(..., description="True if the item passed verification")
    issues: List[str] = Field([], description="List of issues found during verification")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) in the verification result")
