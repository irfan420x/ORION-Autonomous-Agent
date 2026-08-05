from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any

DependencyStatus = Literal["INSTALLED", "MISSING", "OUTDATED", "CORRUPTED", "UNKNOWN"]

class DependencyInfo(BaseModel):
    name: str = Field(..., description="Name of the dependency (e.g., 'nmap', 'pytest', 'psutil')")
    version: Optional[str] = Field(None, description="Installed version of the dependency")
    required_version: Optional[str] = Field(None, description="Required version of the dependency")
    status: DependencyStatus = Field(..., description="Current status of the dependency")
    platform_specific_name: Optional[str] = Field(None, description="Platform-specific name if different from generic name")
    install_command: Optional[str] = Field(None, description="Command to install this dependency")

class DependencyCheckResult(BaseModel):
    dependency: DependencyInfo = Field(..., description="Information about the checked dependency")
    is_ok: bool = Field(..., description="True if dependency is installed and meets requirements")
    message: Optional[str] = Field(None, description="Detailed message about the check result")

class PlatformMapping(BaseModel):
    generic_name: str = Field(..., description="Generic name of the tool/package")
    linux_apt: Optional[str] = Field(None, description="Package name for Debian/Ubuntu")
    macos_brew: Optional[str] = Field(None, description="Package name for macOS Homebrew")
    windows_choco: Optional[str] = Field(None, description="Package name for Windows Chocolatey")
    python_pip: Optional[str] = Field(None, description="Package name for Python pip")
    rust_cargo: Optional[str] = Field(None, description="Crate name for Rust Cargo")

