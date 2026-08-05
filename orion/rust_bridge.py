"""
ORION Rust Bridge
=================

Python wrapper for the orion-rs binary.
Provides async interface to Rust process monitor and file watcher.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Path to the orion-rs binary
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINARY_PATH = os.path.join(_PROJECT_ROOT, "orion-rs", "target", "release", "orion-rs")


class RustBridge:
    """
    Python interface to the orion-rs Rust binary.
    """
    
    def __init__(self, binary_path: Optional[str] = None):
        self._binary = binary_path or BINARY_PATH
        self._available = os.path.isfile(self._binary) and os.access(self._binary, os.X_OK)
        
        if self._available:
            logger.info("RustBridge initialized (binary=%s)", self._binary)
        else:
            logger.warning("RustBridge: binary not found at %s", self._binary)
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    async def _run(self, *args: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Run orion-rs with arguments and return parsed JSON output."""
        if not self._available:
            return {"error": "Binary not available", "available": False}
        
        cmd = [self._binary] + list(args)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            
            if proc.returncode != 0:
                return {"error": stderr.decode().strip(), "returncode": proc.returncode}
            
            output = stdout.decode().strip()
            if not output:
                return {"result": "empty"}
            
            return json.loads(output)
        
        except asyncio.TimeoutError:
            return {"error": "Timeout"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON decode error: {e}", "raw": output}
        except Exception as e:
            return {"error": str(e)}
    
    async def health(self) -> Dict[str, Any]:
        """Quick health check via Rust."""
        return await self._run("health")
    
    async def snapshot(self, top_n: int = 20) -> Dict[str, Any]:
        """Full system snapshot via Rust."""
        return await self._run("snapshot")
    
    async def processes(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """Top N processes by CPU via Rust."""
        result = await self._run("processes", str(top_n))
        if isinstance(result, list):
            return result
        return []
    
    async def watch(self, path: str, seconds: int = 5) -> List[Dict[str, Any]]:
        """Watch a directory for file changes."""
        result = await self._run("watch", path, str(seconds), timeout=seconds + 5)
        if isinstance(result, list):
            return result
        return []
