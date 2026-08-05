"""
ORION Observability Contracts
==============================

Pydantic models for metrics, tracing, and cost tracking.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricValue(BaseModel):
    """A single metric measurement."""
    name: str = Field(..., description="Metric name (e.g., 'cpu_percent')")
    value: float = Field(..., description="Metric value")
    metric_type: MetricType = Field(..., description="Type of metric")
    labels: Dict[str, str] = Field(default_factory=dict, description="Label key-value pairs")
    timestamp: float = Field(..., description="Unix timestamp")
    unit: str = Field("", description="Unit (e.g., 'percent', 'bytes', 'ms')")


class SpanStatus(str, Enum):
    """Status of a trace span."""
    OK = "OK"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class TraceSpan(BaseModel):
    """A single trace span (unit of work)."""
    span_id: str = Field(..., description="Unique span identifier")
    trace_id: str = Field(..., description="Parent trace identifier")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID for nested spans")
    operation: str = Field(..., description="Operation name")
    service: str = Field("orion", description="Service name")
    status: SpanStatus = Field(SpanStatus.OK, description="Span status")
    start_time: float = Field(..., description="Start timestamp")
    end_time: Optional[float] = Field(None, description="End timestamp")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Span events")


class Trace(BaseModel):
    """A complete trace (collection of spans)."""
    trace_id: str = Field(..., description="Unique trace identifier")
    spans: List[TraceSpan] = Field(default_factory=list, description="Spans in this trace")
    start_time: float = Field(..., description="Trace start time")
    end_time: Optional[float] = Field(None, description="Trace end time")
    total_duration_ms: Optional[float] = Field(None, description="Total duration")
    status: SpanStatus = Field(SpanStatus.OK, description="Overall trace status")


class CostEvent(BaseModel):
    """A cost-tracking event (e.g., LLM API call)."""
    event_id: str = Field(..., description="Unique event ID")
    service: str = Field(..., description="Service that incurred cost (e.g., 'openai', 'gemini')")
    operation: str = Field(..., description="Operation (e.g., 'completion', 'embedding')")
    tokens_input: int = Field(0, description="Input tokens used")
    tokens_output: int = Field(0, description="Output tokens used")
    cost_usd: float = Field(0.0, description="Cost in USD")
    model: str = Field("", description="Model used")
    timestamp: float = Field(..., description="When the cost was incurred")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ObservabilityStats(BaseModel):
    """Statistics about the observability system."""
    total_metrics_collected: int = 0
    total_traces: int = 0
    total_spans: int = 0
    total_cost_events: int = 0
    total_cost_usd: float = 0.0
    active_traces: int = 0
    metrics_in_memory: int = 0
