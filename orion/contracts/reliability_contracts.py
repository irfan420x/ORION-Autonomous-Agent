"""
ORION Reliability Contracts
============================

Pydantic models for the Self-Healing Architecture.

Components:
- Health Check results
- Service status tracking
- Recovery actions
- Failure reports
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


class ServiceStatus(str, Enum):
    """Status of a monitored service."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"
    CRASHED = "CRASHED"


class RecoveryAction(str, Enum):
    """Possible recovery actions."""
    NONE = "NONE"
    RESTART = "RESTART"
    RECONNECT = "RECONNECT"
    RESTORE_BACKUP = "RESTORE_BACKUP"
    REINSTALL = "REINSTALL"
    NOTIFY_USER = "NOTIFY_USER"
    ESCALATE = "ESCALATE"


class HealthCheckResult(BaseModel):
    """Result of a single health check."""
    service_name: str = Field(..., description="Name of the service checked")
    status: ServiceStatus = Field(..., description="Current status")
    latency_ms: float = Field(0.0, description="Response latency in milliseconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: float = Field(..., description="Unix timestamp of the check")


class SystemHealthReport(BaseModel):
    """Complete system health report."""
    overall_status: ServiceStatus = Field(..., description="Overall system status")
    services: List[HealthCheckResult] = Field(default_factory=list, description="Individual service results")
    cpu_percent: float = Field(0.0, description="CPU usage percentage")
    ram_percent: float = Field(0.0, description="RAM usage percentage")
    disk_percent: float = Field(0.0, description="Disk usage percentage")
    uptime_seconds: float = Field(0.0, description="System uptime")
    checks_passed: int = Field(0, description="Number of checks passed")
    checks_failed: int = Field(0, description="Number of checks failed")
    timestamp: float = Field(..., description="Unix timestamp of the report")


class FailureReport(BaseModel):
    """Report of a detected failure."""
    failure_id: str = Field(..., description="Unique failure identifier")
    service_name: str = Field(..., description="Service that failed")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    severity: str = Field("medium", description="Severity: low, medium, high, critical")
    timestamp: float = Field(..., description="When the failure occurred")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class RecoveryResult(BaseModel):
    """Result of a recovery attempt."""
    success: bool = Field(..., description="Whether recovery succeeded")
    action_taken: RecoveryAction = Field(..., description="Action that was taken")
    service_name: str = Field(..., description="Service that was recovered")
    details: str = Field("", description="Details about the recovery")
    attempts: int = Field(1, description="Number of attempts made")
    timestamp: float = Field(..., description="When recovery completed")


class IntegrityCheckResult(BaseModel):
    """Result of a data integrity check."""
    file_path: str = Field(..., description="Path to the checked file")
    is_valid: bool = Field(..., description="Whether the file is valid")
    checksum: Optional[str] = Field(None, description="Current checksum")
    expected_checksum: Optional[str] = Field(None, description="Expected checksum")
    file_size_bytes: int = Field(0, description="File size")
    error_message: Optional[str] = Field(None, description="Error if invalid")
    timestamp: float = Field(..., description="When the check was performed")
