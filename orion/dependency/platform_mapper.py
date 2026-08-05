"""
ORION Platform Mapper
=====================

Maps generic tool/package names to platform-specific names.
Handles Linux (apt), macOS (brew), Windows (choco), pip, cargo.
"""

import logging
import platform
from typing import Dict, Optional

from orion.contracts.dependency_contracts import PlatformMapping

logger = logging.getLogger(__name__)

# Known platform mappings
PLATFORM_MAPPINGS: Dict[str, PlatformMapping] = {
    "nmap": PlatformMapping(
        generic_name="nmap",
        linux_apt="nmap",
        macos_brew="nmap",
        windows_choco="nmap",
    ),
    "git": PlatformMapping(
        generic_name="git",
        linux_apt="git",
        macos_brew="git",
        windows_choco="git",
    ),
    "curl": PlatformMapping(
        generic_name="curl",
        linux_apt="curl",
        macos_brew="curl",
        windows_choco="curl",
    ),
    "ffmpeg": PlatformMapping(
        generic_name="ffmpeg",
        linux_apt="ffmpeg",
        macos_brew="ffmpeg",
        windows_choco="ffmpeg",
    ),
    "tshark": PlatformMapping(
        generic_name="tshark",
        linux_apt="tshark",
        macos_brew="wireshark",
        windows_choco="wireshark",
    ),
    "sqlite3": PlatformMapping(
        generic_name="sqlite3",
        linux_apt="sqlite3",
        macos_brew="sqlite",
        windows_choco="sqlite",
    ),
    "node": PlatformMapping(
        generic_name="node",
        linux_apt="nodejs",
        macos_brew="node",
        windows_choco="nodejs",
    ),
    "docker": PlatformMapping(
        generic_name="docker",
        linux_apt="docker.io",
        macos_brew="docker",
        windows_choco="docker-desktop",
    ),
    "psutil": PlatformMapping(
        generic_name="psutil",
        python_pip="psutil",
    ),
    "pydantic": PlatformMapping(
        generic_name="pydantic",
        python_pip="pydantic",
    ),
    "pytest": PlatformMapping(
        generic_name="pytest",
        python_pip="pytest",
    ),
    "requests": PlatformMapping(
        generic_name="requests",
        python_pip="requests",
    ),
    "playwright": PlatformMapping(
        generic_name="playwright",
        python_pip="playwright",
    ),
    "fastapi": PlatformMapping(
        generic_name="fastapi",
        python_pip="fastapi",
    ),
}


class PlatformMapper:
    """
    Maps generic tool names to platform-specific package names.
    """
    
    def __init__(self):
        self._os = platform.system().lower()  # 'linux', 'darwin', 'windows'
        self._custom_mappings: Dict[str, PlatformMapping] = {}
        logger.info("PlatformMapper initialized (OS=%s)", self._os)
    
    def get_package_name(self, generic_name: str) -> Optional[str]:
        """Get the platform-specific package name."""
        mapping = self._get_mapping(generic_name)
        if not mapping:
            return None
        
        if self._os == "linux":
            return mapping.linux_apt or mapping.generic_name
        elif self._os == "darwin":
            return mapping.macos_brew or mapping.generic_name
        elif self._os == "windows":
            return mapping.windows_choco or mapping.generic_name
        
        return mapping.generic_name
    
    def get_install_command(self, generic_name: str) -> Optional[str]:
        """Get the install command for this platform."""
        mapping = self._get_mapping(generic_name)
        if not mapping:
            return None
        
        pkg = self.get_package_name(generic_name)
        
        if mapping.python_pip:
            return f"pip install {mapping.python_pip}"
        elif mapping.rust_cargo:
            return f"cargo install {mapping.rust_cargo}"
        
        if self._os == "linux":
            return f"sudo apt-get install -y {pkg}"
        elif self._os == "darwin":
            return f"brew install {pkg}"
        elif self._os == "windows":
            return f"choco install {pkg}"
        
        return None
    
    def get_pip_name(self, generic_name: str) -> Optional[str]:
        """Get the pip package name if it's a Python package."""
        mapping = self._get_mapping(generic_name)
        return mapping.python_pip if mapping else None
    
    def get_binary_name(self, generic_name: str) -> str:
        """Get the binary/command name (usually same as generic)."""
        return generic_name
    
    def add_mapping(self, mapping: PlatformMapping) -> None:
        """Add a custom platform mapping."""
        self._custom_mappings[mapping.generic_name] = mapping
    
    def _get_mapping(self, generic_name: str) -> Optional[PlatformMapping]:
        """Get the mapping for a generic name."""
        return self._custom_mappings.get(generic_name) or PLATFORM_MAPPINGS.get(generic_name)
    
    def get_all_mappings(self) -> Dict[str, PlatformMapping]:
        """Get all known mappings."""
        all_mappings = dict(PLATFORM_MAPPINGS)
        all_mappings.update(self._custom_mappings)
        return all_mappings
