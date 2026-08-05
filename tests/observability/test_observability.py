"""
Tests for ORION Observability (Metrics, Tracing, Cost)
======================================================
"""

import asyncio
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.contracts.observability_contracts import (
    MetricType,
    MetricValue,
    TraceSpan,
    SpanStatus,
    CostEvent,
)
from orion.observability.metrics_collector import MetricsCollector
from orion.observability.tracer import Tracer
from orion.observability.cost_monitor import CostMonitor


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def collector(event_bus):
    return MetricsCollector(event_bus, collection_interval=0.2)


@pytest.fixture
def tracer(event_bus):
    return Tracer(event_bus)


@pytest.fixture
def cost_monitor(event_bus):
    return CostMonitor(event_bus, monthly_budget=50.0)


# ── Metrics Collector Tests ──────────────────────────────────

class TestMetricsCollector:
    def test_initial_state(self, collector):
        assert not collector._running
        assert collector.get_metric_count() == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, collector):
        await collector.start()
        assert collector._running
        await collector.stop()
        assert not collector._running

    def test_record_metric(self, collector):
        collector.record("test.cpu", 45.0, MetricType.GAUGE, unit="percent")
        assert collector.get_metric_count() == 1
        
        values = collector.query("test.cpu")
        assert len(values) == 1
        assert values[0].value == 45.0

    def test_record_multiple(self, collector):
        for i in range(5):
            collector.gauge("test.metric", float(i))
        
        values = collector.query("test.metric")
        assert len(values) == 5
        assert values[-1].value == 4.0

    def test_increment(self, collector):
        collector.increment("test.counter")
        collector.increment("test.counter")
        collector.increment("test.counter")
        
        values = collector.query("test.counter")
        assert len(values) == 3
        assert values[-1].value == 3.0

    def test_query_with_limit(self, collector):
        for i in range(10):
            collector.gauge("test.limited", float(i))
        
        values = collector.query("test.limited", limit=3)
        assert len(values) == 3

    def test_query_with_since(self, collector):
        now = time.time()
        collector.record("test.old", 1.0, MetricType.GAUGE, timestamp=now - 100)
        collector.record("test.new", 2.0, MetricType.GAUGE, timestamp=now)
        
        values = collector.query("test.new", since=now - 50)
        assert len(values) == 1
        assert values[0].value == 2.0

    def test_query_latest(self, collector):
        collector.gauge("test.gauge", 10.0)
        collector.gauge("test.gauge", 20.0)
        
        latest = collector.query_latest("test.gauge")
        assert latest.value == 20.0

    def test_query_latest_empty(self, collector):
        assert collector.query_latest("nonexistent") is None

    def test_aggregate_avg(self, collector):
        for i in range(5):
            collector.gauge("test.avg", float(i * 10))
        
        avg = collector.aggregate("test.avg", "avg")
        assert avg == 20.0  # (0+10+20+30+40)/5

    def test_aggregate_min_max(self, collector):
        collector.gauge("test.range", 5.0)
        collector.gauge("test.range", 15.0)
        collector.gauge("test.range", 10.0)
        
        assert collector.aggregate("test.range", "min") == 5.0
        assert collector.aggregate("test.range", "max") == 15.0

    def test_aggregate_sum(self, collector):
        collector.gauge("test.sum", 10.0)
        collector.gauge("test.sum", 20.0)
        
        assert collector.aggregate("test.sum", "sum") == 30.0

    def test_aggregate_count(self, collector):
        for _ in range(7):
            collector.gauge("test.count", 1.0)
        
        assert collector.aggregate("test.count", "count") == 7.0

    def test_aggregate_empty(self, collector):
        assert collector.aggregate("nonexistent", "avg") is None

    def test_labels(self, collector):
        collector.gauge("test.labeled", 1.0, labels={"host": "server1"})
        collector.gauge("test.labeled", 2.0, labels={"host": "server2"})
        
        values = collector.query("test.labeled")
        assert len(values) == 2

    def test_max_per_name(self, event_bus):
        c = MetricsCollector(event_bus, max_metrics_per_name=5)
        for i in range(10):
            c.gauge("test.trim", float(i))
        
        values = c.query("test.trim")
        assert len(values) == 5
        assert values[0].value == 5.0  # First 5 trimmed

    @pytest.mark.asyncio
    async def test_auto_collection(self, event_bus):
        c = MetricsCollector(event_bus, collection_interval=0.1)
        await c.start()
        await asyncio.sleep(0.3)
        await c.stop()
        
        names = c.get_all_metric_names()
        assert "system.cpu.percent" in names
        assert "system.ram.percent" in names

    @pytest.mark.asyncio
    async def test_get_stats(self, collector):
        collector.gauge("test.stat", 1.0)
        stats = collector.get_stats()
        
        assert "total_collected" in stats
        assert "distinct_metrics" in stats
        assert stats["total_collected"] == 1


# ── Tracer Tests ─────────────────────────────────────────────

class TestTracer:
    def test_start_trace(self, tracer):
        span = tracer.start_trace("test_op")
        
        assert span.span_id is not None
        assert span.trace_id is not None
        assert span.operation == "test_op"
        assert span.parent_span_id is None

    def test_start_span(self, tracer):
        parent = tracer.start_trace("parent")
        child = tracer.start_span("child", parent_span=parent)
        
        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id

    def test_end_span(self, tracer):
        span = tracer.start_trace("test")
        tracer.end_span(span, SpanStatus.OK)
        
        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms >= 0

    def test_trace_completes_on_root_end(self, tracer):
        span = tracer.start_trace("root")
        tracer.end_span(span)
        
        assert len(tracer.get_active_traces()) == 0
        assert len(tracer.get_completed_traces()) == 1

    def test_nested_spans(self, tracer):
        root = tracer.start_trace("root")
        child1 = tracer.start_span("child1", parent_span=root)
        child2 = tracer.start_span("child2", parent_span=root)
        
        tracer.end_span(child1)
        tracer.end_span(child2)
        tracer.end_span(root)
        
        trace = tracer.get_completed_traces()[0]
        assert len(trace.spans) == 3

    def test_span_attributes(self, tracer):
        span = tracer.start_trace("test", attributes={"key": "value"})
        assert span.attributes["key"] == "value"

    def test_span_event(self, tracer):
        span = tracer.start_trace("test")
        tracer.add_span_event(span, "checkpoint", {"step": 1})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "checkpoint"

    def test_span_status(self, tracer):
        span = tracer.start_trace("test")
        tracer.end_span(span, SpanStatus.ERROR)
        assert span.status == SpanStatus.ERROR

    def test_get_trace(self, tracer):
        span = tracer.start_trace("test")
        trace = tracer.get_trace(span.trace_id)
        assert trace is not None
        assert trace.trace_id == span.trace_id

    def test_get_trace_not_found(self, tracer):
        assert tracer.get_trace("nonexistent") is None

    def test_get_active_traces(self, tracer):
        tracer.start_trace("a")
        tracer.start_trace("b")
        assert len(tracer.get_active_traces()) == 2

    def test_get_completed_traces(self, tracer):
        for i in range(3):
            s = tracer.start_trace(f"t{i}")
            tracer.end_span(s)
        
        assert len(tracer.get_completed_traces()) == 3
        assert len(tracer.get_completed_traces(limit=2)) == 2

    def test_stats(self, tracer):
        s = tracer.start_trace("test")
        tracer.end_span(s)
        
        stats = tracer.get_stats()
        assert stats["total_traces"] == 1
        assert stats["total_spans"] == 1
        assert stats["active_traces"] == 0
        assert stats["completed_traces"] == 1


# ── Cost Monitor Tests ───────────────────────────────────────

class TestCostMonitor:
    def test_record_cost(self, cost_monitor):
        event = cost_monitor.record_cost("openai", "gpt-4", 1000, 500, 0.03)
        
        assert event.service == "openai"
        assert event.model == "gpt-4"
        assert event.cost_usd == 0.03

    def test_total_cost(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 1000, 500, 0.03)
        cost_monitor.record_cost("openai", "gpt-4", 2000, 1000, 0.06)
        
        stats = cost_monitor.get_stats()
        assert stats["total_cost_usd"] == 0.09

    def test_total_tokens(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 1000, 500, 0.03)
        cost_monitor.record_cost("openai", "gpt-4", 2000, 1000, 0.06)
        
        stats = cost_monitor.get_stats()
        assert stats["total_tokens_input"] == 3000
        assert stats["total_tokens_output"] == 1500

    def test_budget_used_percent(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 25.0)
        
        stats = cost_monitor.get_stats()
        assert stats["budget_used_percent"] == 50.0

    def test_report_by_service(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 10.0)
        cost_monitor.record_cost("gemini", "flash", 0, 0, 5.0)
        
        report = cost_monitor.get_report()
        assert report["by_service"]["openai"] == 10.0
        assert report["by_service"]["gemini"] == 5.0

    def test_report_by_model(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 10.0)
        cost_monitor.record_cost("openai", "gpt-3.5", 0, 0, 2.0)
        
        report = cost_monitor.get_report()
        assert report["by_model"]["gpt-4"] == 10.0

    def test_remaining_budget(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 30.0)
        
        report = cost_monitor.get_report()
        assert report["remaining_budget_usd"] == 20.0

    def test_budget_alert(self, cost_monitor):
        # Budget is 50, threshold is 80% = 40
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 45.0)
        
        stats = cost_monitor.get_stats()
        assert stats["budget_used_percent"] == 90.0

    def test_get_recent_events(self, cost_monitor):
        for i in range(5):
            cost_monitor.record_cost("openai", "gpt-4", 0, 0, float(i))
        
        events = cost_monitor.get_recent_events(3)
        assert len(events) == 3

    def test_reset_alert(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 0, 0, 45.0)
        cost_monitor.reset_alert()
        
        report = cost_monitor.get_report()
        assert not report["alert_sent"]

    def test_get_stats(self, cost_monitor):
        cost_monitor.record_cost("openai", "gpt-4", 100, 50, 0.05)
        stats = cost_monitor.get_stats()
        
        assert "total_cost_usd" in stats
        assert "total_events" in stats
        assert stats["total_events"] == 1


# ── Contracts Tests ──────────────────────────────────────────

class TestContracts:
    def test_metric_value(self):
        m = MetricValue(
            name="cpu", value=50.0,
            metric_type=MetricType.GAUGE,
            timestamp=time.time(),
        )
        assert m.name == "cpu"

    def test_trace_span(self):
        s = TraceSpan(
            span_id="abc", trace_id="xyz",
            operation="test", start_time=time.time(),
        )
        assert s.span_id == "abc"

    def test_cost_event(self):
        e = CostEvent(
            event_id="123", service="openai", operation="completion",
            timestamp=time.time(),
        )
        assert e.service == "openai"

    def test_span_status_enum(self):
        assert SpanStatus.OK == "OK"
        assert SpanStatus.ERROR == "ERROR"

    def test_metric_type_enum(self):
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
