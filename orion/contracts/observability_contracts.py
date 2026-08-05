from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class Metric(BaseModel):
    name: str = Field(..., description="Name of the metric (e.g., cpu_usage_percent, llm_tokens_used)")
    value: float = Field(..., description="Value of the metric")
    timestamp: float = Field(..., description="Unix timestamp of when the metric was recorded")
    tags: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for metric categorization")

class Span(BaseModel):
    span_id: str = Field(..., description="Unique identifier for the span")
    trace_id: str = Field(..., description="Unique identifier for the trace")
    name: str = Field(..., description="Name of the operation represented by the span")
    start_time: float = Field(..., description="Unix timestamp of span start")
    end_time: Optional[float] = Field(None, description="Unix timestamp of span end")
    parent_span_id: Optional[str] = Field(None, description="ID of the parent span")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs of span attributes")

class SpanStatus(BaseModel):
    status_code: Literal["UNSET", "OK", "ERROR"] = Field(..., description="Status code of the span")
    description: Optional[str] = Field(None, description="Description of the status")

class LogEntry(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp of the log entry")
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Structured context for the log entry")
    component: str = Field(..., description="Component that generated the log")

class CostEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the cost event")
    timestamp: float = Field(..., description="Unix timestamp of the event")
    source: str = Field(..., description="Source of the cost (e.g., LLM API, cloud service)")
    cost_usd: float = Field(..., description="Cost incurred by the event in USD")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed information about the cost event")
