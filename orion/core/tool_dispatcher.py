"""
ORION Tool Dispatcher
=====================

Dispatches tool calls with budget management, error handling,
and concurrent execution support.

Inspired by Hermes Agent's tool_executor.py patterns.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .error_classifier import classify_error, should_retry, format_error, ErrorCategory

logger = logging.getLogger(__name__)


class ToolResult:
    """Result of a tool execution."""
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        output: str,
        error: Optional[str] = None,
        duration_ms: float = 0,
        truncated: bool = False,
    ):
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms
        self.truncated = truncated
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "output": self.output[:500] if self.truncated else self.output,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 1),
        }
    
    def to_message(self) -> str:
        """Format for LLM context."""
        if self.success:
            return f"Tool '{self.tool_name}' result:\n{self.output}"
        else:
            return f"Tool '{self.tool_name}' error: {self.error}"


class ToolDispatcher:
    """
    Dispatches tool calls with error handling and budget management.
    """
    
    # Max output size per tool result (chars)
    MAX_OUTPUT_SIZE = 4000
    
    # Max total output budget per turn
    MAX_TURN_BUDGET = 20000
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: List[Dict[str, Any]] = []
        self._turn_budget_used: int = 0
    
    def register(self, name: str, handler: Callable, schema: Optional[Dict] = None):
        """Register a tool."""
        self._tools[name] = handler
        if schema:
            self._tool_schemas.append(schema)
        logger.debug("Tool registered: %s", name)
    
    def reset_budget(self):
        """Reset turn budget."""
        self._turn_budget_used = 0
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a single tool with error handling.
        """
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}",
            )
        
        handler = self._tools[tool_name]
        start_time = time.time()
        
        try:
            # Execute tool
            if asyncio.iscoroutinefunction(handler):
                output = await handler(**arguments)
            else:
                output = handler(**arguments)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Truncate if too large
            output_str = str(output)
            truncated = False
            if len(output_str) > self.MAX_OUTPUT_SIZE:
                output_str = output_str[:self.MAX_OUTPUT_SIZE] + "\n... (truncated)"
                truncated = True
            
            # Check budget
            if self._turn_budget_used + len(output_str) > self.MAX_TURN_BUDGET:
                output_str = output_str[:self.MAX_TURN_BUDGET - self._turn_budget_used] + "\n... (budget limit)"
                truncated = True
            
            self._turn_budget_used += len(output_str)
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output_str,
                duration_ms=duration_ms,
                truncated=truncated,
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category, strategy = classify_error(e)
            
            logger.error(
                "Tool '%s' failed (%s): %s",
                tool_name, category.value, str(e)[:100]
            )
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=format_error(e),
                duration_ms=duration_ms,
            )
    
    async def execute_batch(
        self,
        calls: List[Tuple[str, Dict[str, Any]]],
        concurrent: bool = False,
    ) -> List[ToolResult]:
        """
        Execute multiple tool calls.
        
        Args:
            calls: List of (tool_name, arguments) tuples
            concurrent: If True, execute in parallel
        """
        if concurrent:
            tasks = [self.execute(name, args) for name, args in calls]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for name, args in calls:
                result = await self.execute(name, args)
                results.append(result)
            return results
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for LLM."""
        return self._tool_schemas
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        return {
            "registered_tools": len(self._tools),
            "turn_budget_used": self._turn_budget_used,
            "turn_budget_max": self.MAX_TURN_BUDGET,
        }
