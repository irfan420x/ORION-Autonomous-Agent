from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class FailureReport(BaseModel):
    task_id: str = Field(..., description="ID of the task that failed")
    error_type: str = Field(..., description="Type of error encountered")
    error_message: str = Field(..., description="Detailed error message")
    context: Dict[str, Any] = Field({}, description="Contextual information at the time of failure")
    recovery_attempted: bool = Field(False, description="True if recovery was attempted")
    recovery_successful: bool = Field(False, description="True if recovery was successful")
    timestamp: float = Field(..., description="Unix timestamp of the failure")

class LearningFeedback(BaseModel):
    feedback_type: Literal["failure", "success", "user_rating", "performance_metric"] = Field(..., description="Type of feedback")
    payload: Dict[str, Any] = Field(..., description="Feedback-specific data")
    timestamp: float = Field(..., description="Unix timestamp of the feedback")

class LearningStrategy(BaseModel):
    strategy_id: str = Field(..., description="Unique identifier for the learned strategy")
    description: str = Field(..., description="Description of the strategy")
    conditions: Dict[str, Any] = Field(..., description="Conditions under which this strategy is applicable")
    actions: List[Dict[str, Any]] = Field(..., description="Actions to take as part of this strategy")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) in the effectiveness of this strategy")
    last_updated: float = Field(..., description="Unix timestamp of last update")

class PromptOptimizationResult(BaseModel):
    original_prompt: str = Field(..., description="The original prompt")
    optimized_prompt: str = Field(..., description="The optimized prompt")
    improvement_score: float = Field(..., description="Score indicating the improvement (e.0-1.0)")
    reason: Optional[str] = Field(None, description="Reason for the optimization")
