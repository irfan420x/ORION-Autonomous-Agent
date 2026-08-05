from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class FileNode(BaseModel):
    path: str = Field(..., description="Absolute path of the file or directory")
    name: str = Field(..., description="Name of the file or directory")
    is_dir: bool = Field(..., description="True if it's a directory, False if a file")
    size: Optional[int] = Field(None, description="Size in bytes if it's a file")
    last_modified: Optional[float] = Field(None, description="Unix timestamp of last modification")
    children: Optional[List[str]] = Field(None, description="List of child paths if it's a directory")

class ProcessNode(BaseModel):
    pid: int = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    cmdline: List[str] = Field(..., description="Command line arguments")
    status: str = Field(..., description="Current status of the process")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    parent_pid: Optional[int] = Field(None, description="Parent process ID")

class NetworkConnection(BaseModel):
    local_address: str = Field(..., description="Local IP address and port")
    remote_address: Optional[str] = Field(None, description="Remote IP address and port")
    status: str = Field(..., description="Status of the connection (e.g., ESTABLISHED, LISTEN)")
    pid: Optional[int] = Field(None, description="Process ID associated with the connection")

class GitStatus(BaseModel):
    repo_path: str = Field(..., description="Path to the Git repository")
    is_dirty: bool = Field(..., description="True if there are uncommitted changes")
    current_branch: str = Field(..., description="Name of the current branch")
    last_commit_msg: Optional[str] = Field(None, description="Message of the last commit")
    untracked_files: List[str] = Field(default_factory=list, description="List of untracked files")

class WindowInfo(BaseModel):
    window_id: str = Field(..., description="Platform-specific window identifier")
    title: str = Field(..., description="Title of the window")
    process_name: str = Field(..., description="Name of the process owning the window")
    is_active: bool = Field(..., description="True if this is the currently active window")
    bounds: Dict[str, int] = Field(..., description="x, y, width, height of the window")

class WorldModelGraph(BaseModel):
    graph_type: str = Field(..., description="Type of the graph (e.g., 'filesystem', 'process')")
    nodes: List[Dict[str, Any]] = Field(..., description="List of nodes in the graph")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="List of edges in the graph")
