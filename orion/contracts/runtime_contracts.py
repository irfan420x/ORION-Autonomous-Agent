from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class HardwareProfile(BaseModel):
    cpu_cores: int = Field(..., description="Number of CPU cores")
    total_ram_gb: float = Field(..., description="Total RAM in GB")
    has_gpu: bool = Field(..., description="True if a GPU is detected")
    gpu_model: Optional[str] = Field(None, description="Model of the GPU if detected")
    internet_connected: bool = Field(..., description="True if internet connectivity is detected")
    os_name: str = Field(..., description="Operating System name, e.g., Linux, Windows, macOS")
    os_version: str = Field(..., description="Operating System version")

OperatingMode = Literal["full", "cpu_only", "low_memory", "offline", "server", "safe"]

class SystemConfig(BaseModel):
    platform: str = Field(..., description="Operating system platform (e.g., 'Linux', 'Windows', 'Darwin')")
    operating_mode: OperatingMode = Field("full", description="Current operating mode of ORION")
    lazy_loading_enabled: bool = Field(True, description="Whether modules should be loaded on demand")
    resource_budget_enabled: bool = Field(True, description="Whether resource usage should be budgeted")
    safe_mode_enabled: bool = Field(False, description="Enables restricted safe mode for critical operations")
