from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class ScheduleDefinition(BaseModel):
    schedule_type: Literal["once", "interval", "cron"] = Field(..., description="Type of schedule")
    run_at: Optional[float] = Field(None, description="Unix timestamp for 'once' schedule")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds for 'interval' schedule")
    cron_expression: Optional[str] = Field(None, description="Cron expression for 'cron' schedule")

class WatcherConfig(BaseModel):
    watcher_id: str = Field(..., description="Unique identifier for the watcher")
    watch_type: Literal["filesystem", "process", "metric"] = Field(..., description="Type of event to watch")
    target: str = Field(..., description="Target to watch (e.g., file path, process name, metric name)")
    trigger_condition: Dict[str, Any] = Field(..., description="Condition that triggers an action (e.g., {"event": "modified", "threshold": 0.8})")
    action_to_trigger: Dict[str, Any] = Field(..., description="Action to perform when triggered (e.g., {"type": "execute_task", "task_id": "cleanup_logs"})")
    is_active: bool = Field(True, description="Whether the watcher is currently active")

class WatcherEvent(BaseModel):
    watcher_id: str = Field(..., description="ID of the watcher that triggered the event")
    event_type: str = Field(..., description="Type of event detected (e.g., file.modified, process.stopped, metric.threshold_exceeded)")
    timestamp: float = Field(..., description="Unix timestamp of the event")
    details: Dict[str, Any] = Field({}, description="Detailed information about the event")

class Report(BaseModel):
    report_id: str = Field(..., description="Unique identifier for the report")
    report_type: str = Field(..., description="Type of report (e.g., 'daily_summary', 'task_performance')")
    period: Optional[str] = Field(None, description="Time period covered by the report (e.g., 'daily', 'weekly')")
    generated_at: float = Field(..., description="Unix timestamp of report generation")
    content: str = Field(..., description="Content of the report (e.g., Markdown, JSON)")
    attachments: List[str] = Field([], description="List of file paths to attachments")
