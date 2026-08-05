"""
ORION Tracing Engine
====================

Distributed tracing for tracking task execution flow.
Creates spans for operations and links them into traces.

Features:
- Trace/span creation with auto-generated IDs
- Nested spans (parent-child)
- Duration tracking
- Status tracking (OK, ERROR, TIMEOUT)
- Event publishing via EventBus

Usage:
    tracer = Tracer(event_bus)
    span = tracer.start_span("process_task", attributes={"task_id": "123"})
    # ... do work ...
    tracer.end_span(span, status=SpanStatus.OK)
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from orion.contracts.observability_contracts import (
    Trace,
    TraceSpan,
    SpanStatus,
)
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class Tracer:
    """
    Distributed tracer for ORION task execution.
    """
    
    def __init__(self, event_bus: EventBus, max_traces: int = 100):
        self._event_bus = event_bus
        self._max_traces = max_traces
        
        # Active traces
        self._traces: Dict[str, Trace] = {}
        
        # Completed traces (for history)
        self._completed_traces: List[Trace] = []
        
        # Stats
        self._total_spans: int = 0
        self._total_traces: int = 0
        
        logger.info("Tracer created")
    
    def start_trace(self, operation: str, attributes: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """Start a new trace with a root span."""
        trace_id = uuid.uuid4().hex[:16]
        span_id = uuid.uuid4().hex[:8]
        now = time.time()
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            operation=operation,
            status=SpanStatus.OK,
            start_time=now,
            attributes=attributes or {},
        )
        
        trace = Trace(
            trace_id=trace_id,
            spans=[span],
            start_time=now,
        )
        
        self._traces[trace_id] = trace
        self._total_traces += 1
        self._total_spans += 1
        
        logger.debug("Started trace %s, span %s: %s", trace_id, span_id, operation)
        return span
    
    def start_span(
        self,
        operation: str,
        parent_span: Optional[TraceSpan] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TraceSpan:
        """Start a new span, optionally as a child of another span."""
        now = time.time()
        
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            # Create a new trace
            trace_id = uuid.uuid4().hex[:16]
            parent_span_id = None
            self._total_traces += 1
        
        span_id = uuid.uuid4().hex[:8]
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation=operation,
            status=SpanStatus.OK,
            start_time=now,
            attributes=attributes or {},
        )
        
        # Add to trace
        if trace_id not in self._traces:
            self._traces[trace_id] = Trace(
                trace_id=trace_id,
                start_time=now,
            )
        
        self._traces[trace_id].spans.append(span)
        self._total_spans += 1
        
        logger.debug("Started span %s in trace %s: %s", span_id, trace_id, operation)
        return span
    
    def end_span(
        self,
        span: TraceSpan,
        status: SpanStatus = SpanStatus.OK,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End a span and calculate its duration."""
        now = time.time()
        span.end_time = now
        span.duration_ms = round((now - span.start_time) * 1000, 2)
        span.status = status
        
        if attributes:
            span.attributes.update(attributes)
        
        # Check if trace is complete (root span ended)
        trace = self._traces.get(span.trace_id)
        if trace and not span.parent_span_id:
            trace.end_time = now
            trace.total_duration_ms = round((now - trace.start_time) * 1000, 2)
            trace.status = status
            
            # Move to completed
            self._completed_traces.append(trace)
            if len(self._completed_traces) > self._max_traces:
                self._completed_traces.pop(0)
            del self._traces[span.trace_id]
        
        logger.debug(
            "Ended span %s: %s (%.1fms, %s)",
            span.span_id, span.operation, span.duration_ms, status.value
        )
    
    def add_span_event(
        self,
        span: TraceSpan,
        event_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an event to a span."""
        span.events.append({
            "name": event_name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID (active or completed)."""
        if trace_id in self._traces:
            return self._traces[trace_id]
        for t in self._completed_traces:
            if t.trace_id == trace_id:
                return t
        return None
    
    def get_active_traces(self) -> List[Trace]:
        """Get all active (in-progress) traces."""
        return list(self._traces.values())
    
    def get_completed_traces(self, limit: int = 10) -> List[Trace]:
        """Get recent completed traces."""
        return self._completed_traces[-limit:]
    
    # ── Statistics ────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracer statistics."""
        return {
            "total_traces": self._total_traces,
            "total_spans": self._total_spans,
            "active_traces": len(self._traces),
            "completed_traces": len(self._completed_traces),
        }
