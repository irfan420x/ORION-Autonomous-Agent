from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

class CPUUsage(BaseModel):
    percent: float = Field(..., description="Current CPU usage percentage")
    per_cpu_percent: Dict[int, float] = Field(..., description="CPU usage percentage per core")

class MemoryUsage(BaseModel):
    total_gb: float = Field(..., description="Total system memory in GB")
    available_gb: float = Field(..., description="Available system memory in GB")
    used_percent: float = Field(..., description="Percentage of memory used")

class DiskUsage(BaseModel):
    path: str = Field(..., description="Path for which disk usage is reported")
    total_gb: float = Field(..., description="Total disk space in GB")
    used_gb: float = Field(..., description="Used disk space in GB")
    free_gb: float = Field(..., description="Free disk space in GB")
    used_percent: float = Field(..., description="Percentage of disk space used")

ResourceType = Literal["cpu", "memory", "disk", "network"]

class ResourceLimit(BaseModel):
    resource_type: ResourceType = Field(..., description="Type of resource to limit")
    limit_value: Any = Field(..., description="The value of the limit (e.g., float for CPU, int for memory in MB)")
    unit: Optional[str] = Field(None, description="Unit of the limit value (e.g., %, MB)")
