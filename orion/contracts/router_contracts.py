from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class ModelInfo(BaseModel):
    model_id: str = Field(..., description="Unique identifier for the model")
    provider: str = Field(..., description="Provider of the model (e.g., 'openai', 'anthropic', 'ollama')")
    type: Literal["llm", "embedding", "vision", "tts"] = Field(..., description="Type of the model")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities (e.g., 'code_generation', 'multimodal')")
    cost_per_token_input: float = Field(0.0, description="Cost per input token in USD")
    cost_per_token_output: float = Field(0.0, description="Cost per output token in USD")
    max_tokens: int = Field(..., description="Maximum context window size in tokens")
    is_local: bool = Field(False, description="True if the model can run locally")
    is_available: bool = Field(True, description="True if the model is currently available")
    latency_ms: Optional[int] = Field(None, description="Average latency in milliseconds")

class LLMRequest(BaseModel):
    prompt: str = Field(..., description="The prompt for the LLM")
    model_id: Optional[str] = Field(None, description="Preferred model ID, if any")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    task_type: str = Field("general", description="Type of task (e.g., 'code_generation', 'summarization')")

class LLMResponse(BaseModel):
    model_id: str = Field(..., description="ID of the model that generated the response")
    text: str = Field(..., description="Generated text response")
    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    cost: float = Field(..., description="Estimated cost of the request in USD")
    finish_reason: str = Field(..., description="Reason for the model finishing generation")

class CostReport(BaseModel):
    current_month_usd: float = Field(..., description="Total cost incurred in the current month in USD")
    monthly_budget_usd: float = Field(..., description="Configured monthly budget in USD")
    remaining_budget_usd: float = Field(..., description="Remaining budget for the current month in USD")
    exceeded_budget: bool = Field(..., description="True if the budget has been exceeded")
    last_updated: float = Field(..., description="Unix timestamp of the last update")
