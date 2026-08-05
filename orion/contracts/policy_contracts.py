from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

class ExecutionStrategy(BaseModel):
    strategy_id: str = Field(..., description="Unique identifier for the execution strategy")
    llm_model: str = Field(..., description="Recommended LLM model to use (e.g., 'claude-3-opus', 'ollama-llama3')")
    tool_selection_policy: Literal["strict", "flexible"] = Field("flexible", description="Policy for selecting tools")
    resource_allocation: Dict[str, Any] = Field(default_factory=dict, description="Recommended resource allocation (e.g., {'cpu_limit': '80%', 'ram_limit_gb': 4})")
    fallback_strategy: Optional[str] = Field(None, description="Fallback strategy if primary fails")
    reason: str = Field(..., description="Explanation for why this strategy was chosen")

class PolicyRule(BaseModel):
    rule_id: str = Field(..., description="Unique identifier for the policy rule")
    condition: Dict[str, Any] = Field(..., description="Conditions that trigger this rule (e.g., {'operating_mode': 'cpu_only', 'cost_exceeded': True})")
    action: Dict[str, Any] = Field(..., description="Actions to take if the condition is met (e.g., {'set_llm_model': 'ollama-llama3', 'disable_vision': True})")
    priority: int = Field(5, description="Priority of the rule, higher means evaluated first")
    description: Optional[str] = Field(None, description="Description of the policy rule")

class PolicyEvaluationResult(BaseModel):
    rule_id: str = Field(..., description="ID of the rule that was evaluated")
    matched: bool = Field(..., description="True if the rule's condition was met")
    applied_actions: List[Dict[str, Any]] = Field(default_factory=list, description="List of actions applied by this rule")
    reason: Optional[str] = Field(None, description="Reason for the evaluation result")
