from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PluginManifest(BaseModel):
    plugin_id: str = Field(..., description="Unique identifier for the plugin")
    name: str = Field(..., description="Human-readable name of the plugin")
    version: str = Field("1.0", description="Version of the plugin")
    author: str = Field(..., description="Author of the plugin")
    description: str = Field(..., description="Detailed description of what the plugin does")
    entry_point: str = Field(..., description="Path to the main file or function to execute when activating the plugin")
    required_capabilities: List[str] = Field(default_factory=list, description="List of ORION capabilities required by this plugin")
    dependencies: List[str] = Field(default_factory=list, description="List of external dependencies (e.g., Python packages, system binaries) required by this plugin")
    permissions_requested: List[str] = Field(default_factory=list, description="List of specific permissions this plugin requests (e.g., 'filesystem.read', 'network.access')")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for plugin-specific configuration")

class PluginStatus(BaseModel):
    plugin_id: str = Field(..., description="Unique identifier for the plugin")
    is_loaded: bool = Field(..., description="True if the plugin is loaded into ORION's memory")
    is_active: bool = Field(..., description="True if the plugin's functionalities are currently active")
    health_status: str = Field("HEALTHY", description="Current health status of the plugin")
    error_message: Optional[str] = Field(None, description="Last error message if the plugin is unhealthy")
