# CLAUDE.md - Observability Subsystem

## 1. Overview
ORION's Observability Subsystem provides deep insights into the agent's internal state and behavior, crucial for debugging, performance optimization, and proactive issue resolution. It encompasses metrics collection, distributed tracing, structured logging, and cost monitoring.

## 2. Components
- **MetricsCollector (`metrics_collector.py`):** Gathers various system and application-level metrics (CPU, RAM, LLM token usage, task latency).
- **Tracer (`tracer.py`):** Implements distributed tracing using OpenTelemetry to track end-to-end execution flow across agents and modules.
- **StructuredLogger (`structured_logger.py`):** Provides a standardized interface for logging events in a structured (e.g., JSON) format, enhancing log analysis.
- **CostMonitor (`cost_monitor.py`):** Monitors and reports on the financial cost incurred by LLM API calls and other cloud services.

## 3. Interfaces (Contracts)
Observability-related data structures are defined in `orion/contracts/observability_contracts.py`.

### 3.1 MetricsCollector Interface
- `async record_metric(metric: Metric)`: Records a specific metric value.
- `async get_metrics() -> List[Metric]`: Retrieves current metric values.

### 3.2 Tracer Interface
- `async start_span(name: str, parent_span_id: Optional[str] = None) -> Span`: Starts a new trace span.
- `async end_span(span: Span, status: SpanStatus)`: Ends a trace span with a given status.

### 3.3 StructuredLogger Interface
- `async log(level: LogLevel, message: str, context: Dict[str, Any])`: Logs a structured message.

### 3.4 CostMonitor Interface
- `async record_cost_event(event: CostEvent)`: Records an event that incurs cost.
- `async get_cost_report() -> CostReport`: Retrieves a summary of costs.

## 4. Dependencies
- **Internal:** `orion.contracts.observability_contracts`, `orion.core.communication.event_bus`, `orion.contracts.router_contracts`
- **External:** `prometheus_client`, `opentelemetry-sdk`, `structlog`, `asyncio`.

## 5. Build Order & Verification (Phase 7 - M7.5)
1. Define observability-related Pydantic models in `orion/contracts/observability_contracts.py`.
2. Implement `StructuredLogger` for JSON-formatted logging.
3. Implement `MetricsCollector` to track basic CPU/RAM usage and custom metrics.
4. Implement `Tracer` with basic OpenTelemetry span creation.
5. Implement `CostMonitor` to integrate with `ModelRouter` for cost tracking.
6. Create a demo script (`examples/observability_demo.py`) to demonstrate logging, metrics, and tracing.
7. Ensure unit tests for all Observability modules pass.
