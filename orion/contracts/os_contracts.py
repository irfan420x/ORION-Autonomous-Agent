from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class FileOperationResult(BaseModel):
    success: bool = Field(..., description="True if the file operation was successful")
    path: str = Field(..., description="Path of the file or directory involved")
    message: Optional[str] = Field(None, description="Detailed message about the operation result")
    content: Optional[str] = Field(None, description="Content read from the file, if applicable")

class ProcessInfo(BaseModel):
    pid: int = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    cmdline: List[str] = Field(..., description="Command line arguments")
    status: str = Field(..., description="Current status of the process")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    parent_pid: Optional[int] = Field(None, description="Parent process ID")

class CommandResult(BaseModel):
    success: bool = Field(..., description="True if the command executed successfully")
    stdout: str = Field(..., description="Standard output from the command")
    stderr: str = Field(..., description="Standard error from the command")
    return_code: int = Field(..., description="Return code of the command execution")
    command: str = Field(..., description="The command that was executed")

class WindowInfo(BaseModel):
    window_id: str = Field(..., description="Platform-specific window identifier")
    title: str = Field(..., description="Title of the window")
    process_name: str = Field(..., description="Name of the process owning the window")
    is_active: bool = Field(..., description="True if this is the currently active window")
    bounds: Dict[str, int] = Field(..., description="x, y, width, height of the window")
