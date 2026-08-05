"""
ORION Reasoning Engine
=====================

Self-correction and reflection capabilities.
Analyzes task results, identifies errors, and suggests fixes.

Features:
- Result verification
- Error analysis and root cause detection
- Self-reflection on decisions
- Improvement suggestions
- Integration with EpisodicMemory for learning

Usage:
    reasoner = ReasoningEngine(llm_client, event_bus)
    result = await reasoner.analyze(task_result)
    if result["needs_correction"]:
        fix = await reasoner.suggest_fix(result)
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus
from orion.intelligence.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class ReasoningResult:
    """Result of a reasoning/analysis operation."""
    
    def __init__(
        self,
        is_valid: bool,
        confidence: float,
        issues: List[str],
        suggestions: List[str],
        reasoning: str,
        needs_correction: bool = False,
    ):
        self.is_valid = is_valid
        self.confidence = confidence  # 0.0 - 1.0
        self.issues = issues
        self.suggestions = suggestions
        self.reasoning = reasoning
        self.needs_correction = needs_correction
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "reasoning": self.reasoning,
            "needs_correction": self.needs_correction,
        }


class ReasoningEngine:
    """
    Analyzes results and provides self-correction.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        llm_client: Optional[LLMClient] = None,
    ):
        self._event_bus = event_bus
        self._llm = llm_client
        
        # Stats
        self._total_analyses: int = 0
        self._total_issues_found: int = 0
        self._total_corrections: int = 0
        
        logger.info("ReasoningEngine initialized (llm=%s)", 
                    "available" if llm_client else "none")
    
    async def analyze_result(
        self,
        task_description: str,
        task_result: str,
        expected_outcome: Optional[str] = None,
    ) -> ReasoningResult:
        """
        Analyze a task result for correctness and quality.
        """
        self._total_analyses += 1
        
        if self._llm:
            try:
                return await self._llm_analyze(task_description, task_result, expected_outcome)
            except Exception as e:
                logger.warning("LLM analysis failed, using heuristic: %s", e)
        
        return self._heuristic_analyze(task_description, task_result, expected_outcome)
    
    async def _llm_analyze(
        self,
        task_description: str,
        task_result: str,
        expected_outcome: Optional[str],
    ) -> ReasoningResult:
        """Use LLM to analyze task result."""
        system_prompt = """You are a quality assurance engine. Analyze the task result and determine if it's correct.

Return a JSON object:
{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of issues found"],
  "suggestions": ["list of improvement suggestions"],
  "reasoning": "explanation of your analysis",
  "needs_correction": true/false
}

Return ONLY the JSON object."""
        
        prompt = f"Task: {task_description}\n\nResult: {task_result}"
        if expected_outcome:
            prompt += f"\n\nExpected: {expected_outcome}"
        
        response = await self._llm.chat(
            prompt=prompt,
            system=system_prompt,
            model="mimo-v2.5-pro",
        )
        
        import json
        text = response.content.strip()
        
        # Extract JSON
        if "{" in text and "}" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
            
            result = ReasoningResult(
                is_valid=data.get("is_valid", True),
                confidence=data.get("confidence", 0.5),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                reasoning=data.get("reasoning", ""),
                needs_correction=data.get("needs_correction", False),
            )
            
            if result.issues:
                self._total_issues_found += len(result.issues)
            if result.needs_correction:
                self._total_corrections += 1
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="intelligence.reasoning.analysis",
                payload=result.to_dict(),
                timestamp=time.time(),
                source="reasoning_engine",
            ))
            
            return result
        
        raise ValueError("Failed to parse LLM response")
    
    def _heuristic_analyze(
        self,
        task_description: str,
        task_result: str,
        expected_outcome: Optional[str],
    ) -> ReasoningResult:
        """Simple heuristic analysis when LLM is not available."""
        issues = []
        suggestions = []
        
        # Check for common error patterns
        error_indicators = ["error", "failed", "exception", "traceback", "❌"]
        for indicator in error_indicators:
            if indicator.lower() in task_result.lower():
                issues.append(f"Result contains error indicator: '{indicator}'")
        
        # Check if result is too short
        if len(task_result.strip()) < 10:
            issues.append("Result is suspiciously short")
            suggestions.append("Verify the task completed successfully")
        
        # Check if expected outcome matches
        if expected_outcome:
            if expected_outcome.lower() not in task_result.lower():
                issues.append("Expected outcome not found in result")
                suggestions.append(f"Result should contain: {expected_outcome}")
        
        is_valid = len(issues) == 0
        confidence = 0.7 if is_valid else 0.3
        
        return ReasoningResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            reasoning="Heuristic analysis (LLM not available)",
            needs_correction=len(issues) > 0,
        )
    
    async def suggest_fix(
        self,
        analysis: ReasoningResult,
        task_description: Optional[str] = None,
    ) -> str:
        """Suggest a fix based on analysis."""
        if not self._llm:
            return "Manual review recommended. Issues: " + "; ".join(analysis.issues)
        
        system_prompt = """You are a debugging assistant. Given the issues found in a task, suggest a concrete fix.
Be specific and actionable. Return ONLY the fix suggestion, no preamble."""
        
        prompt = f"Issues: {', '.join(analysis.issues)}\n\nSuggestions: {', '.join(analysis.suggestions)}"
        if task_description:
            prompt = f"Task: {task_description}\n\n{prompt}"
        
        response = await self._llm.chat(
            prompt=prompt,
            system=system_prompt,
            model="mimo-v2.5-pro",
        )
        
        return response.content.strip()
    
    async def reflect(
        self,
        action_taken: str,
        outcome: str,
        context: Optional[str] = None,
    ) -> ReasoningResult:
        """
        Reflect on an action and its outcome for learning.
        """
        if not self._llm:
            return ReasoningResult(
                is_valid=True,
                confidence=0.5,
                issues=[],
                suggestions=[],
                reasoning="Reflection requires LLM",
            )
        
        system_prompt = """You are a reflection engine. Analyze an action and its outcome to extract lessons.
Return JSON:
{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["what went wrong"],
  "suggestions": ["what to do differently next time"],
  "reasoning": "key takeaway"
}"""
        
        prompt = f"Action: {action_taken}\nOutcome: {outcome}"
        if context:
            prompt += f"\nContext: {context}"
        
        response = await self._llm.chat(
            prompt=prompt,
            system=system_prompt,
            model="mimo-v2.5",
        )
        
        import json
        text = response.content.strip()
        if "{" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
            return ReasoningResult(
                is_valid=data.get("is_valid", True),
                confidence=data.get("confidence", 0.5),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                reasoning=data.get("reasoning", ""),
            )
        
        return ReasoningResult(True, 0.5, [], [], "Reflection completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reasoning engine statistics."""
        return {
            "total_analyses": self._total_analyses,
            "total_issues_found": self._total_issues_found,
            "total_corrections": self._total_corrections,
            "llm_available": self._llm is not None,
        }
