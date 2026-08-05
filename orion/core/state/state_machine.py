"""
ORION Finite State Machine
==========================

Manages the lifecycle states of ORION and its components.

States:
- IDLE: System is waiting for tasks
- PROCESSING: System is actively working on a task
- PAUSED: System is paused (user intervention)
- ERROR: System encountered an error
- SHUTDOWN: System is shutting down

Usage:
    sm = StateMachine(event_bus)
    await sm.start()
    await sm.transition_to(State.PROCESSING)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class State(str, Enum):
    """Possible states for ORION system."""
    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: State
    to_state: State
    timestamp: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateMachine:
    """
    Finite State Machine for ORION system lifecycle management.
    
    Features:
    - Valid state transitions (not all transitions are allowed)
    - Transition history for debugging
    - Event publishing on state changes
    - Guard conditions for transitions
    """
    
    # Valid transitions: from_state -> [allowed_to_states]
    VALID_TRANSITIONS: Dict[State, List[State]] = {
        State.IDLE: [State.PROCESSING, State.SHUTDOWN],
        State.PROCESSING: [State.IDLE, State.PAUSED, State.ERROR],
        State.PAUSED: [State.IDLE, State.PROCESSING, State.SHUTDOWN],
        State.ERROR: [State.IDLE, State.SHUTDOWN],
        State.SHUTDOWN: [],  # No transitions from SHUTDOWN
    }
    
    def __init__(self, event_bus: EventBus, initial_state: State = State.IDLE):
        """
        Initialize the State Machine.
        
        Args:
            event_bus: EventBus for publishing state change events.
            initial_state: Starting state (default: IDLE).
        """
        self._event_bus = event_bus
        self._current_state: State = initial_state
        self._history: List[StateTransition] = []
        self._state_enter_callbacks: Dict[State, List[Callable]] = {}
        self._state_exit_callbacks: Dict[State, List[Callable]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("StateMachine initialized in state: %s", initial_state.value)
    
    @property
    def current_state(self) -> State:
        """Get the current state."""
        return self._current_state
    
    @property
    def history(self) -> List[StateTransition]:
        """Get the transition history."""
        return self._history.copy()
    
    async def start(self) -> None:
        """Start the state machine and publish initial state."""
        await self._event_bus.publish(Event(
            event_type="state.initialized",
            payload={"state": self._current_state.value},
            timestamp=time.time(),
            source="state_machine",
        ))
        logger.info("StateMachine started")
    
    async def transition_to(self, new_state: State, reason: str = "", **metadata) -> bool:
        """
        Transition to a new state.
        
        Args:
            new_state: The target state.
            reason: Reason for the transition.
            **metadata: Additional metadata to store with the transition.
            
        Returns:
            True if transition was successful, False if invalid.
        """
        async with self._lock:
            # Check if transition is valid
            if new_state not in self.VALID_TRANSITIONS.get(self._current_state, []):
                logger.warning(
                    "Invalid transition: %s -> %s",
                    self._current_state.value,
                    new_state.value
                )
                return False
            
            # Execute exit callbacks for current state
            await self._execute_callbacks(self._state_exit_callbacks.get(self._current_state, []))
            
            # Record transition
            transition = StateTransition(
                from_state=self._current_state,
                to_state=new_state,
                timestamp=time.time(),
                reason=reason,
                metadata=metadata,
            )
            self._history.append(transition)
            
            # Update state
            old_state = self._current_state
            self._current_state = new_state
            
            # Execute enter callbacks for new state
            await self._execute_callbacks(self._state_enter_callbacks.get(new_state, []))
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="state.changed",
                payload={
                    "from_state": old_state.value,
                    "to_state": new_state.value,
                    "reason": reason,
                    "metadata": metadata,
                },
                timestamp=time.time(),
                source="state_machine",
            ))
            
            logger.info("State transition: %s -> %s (%s)", old_state.value, new_state.value, reason)
            return True
    
    async def _execute_callbacks(self, callbacks: List[Callable]) -> None:
        """Execute a list of callbacks."""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error("Callback error: %s", str(e))
    
    def on_enter(self, state: State, callback: Callable) -> None:
        """
        Register a callback for when entering a state.
        
        Args:
            state: The state to watch.
            callback: Function to call when entering the state.
        """
        if state not in self._state_enter_callbacks:
            self._state_enter_callbacks[state] = []
        self._state_enter_callbacks[state].append(callback)
        logger.debug("Registered enter callback for state: %s", state.value)
    
    def on_exit(self, state: State, callback: Callable) -> None:
        """
        Register a callback for when exiting a state.
        
        Args:
            state: The state to watch.
            callback: Function to call when exiting the state.
        """
        if state not in self._state_exit_callbacks:
            self._state_exit_callbacks[state] = []
        self._state_exit_callbacks[state].append(callback)
        logger.debug("Registered exit callback for state: %s", state.value)
    
    def get_valid_transitions(self) -> List[State]:
        """
        Get list of states we can transition to from current state.
        
        Returns:
            List of valid target states.
        """
        return self.VALID_TRANSITIONS.get(self._current_state, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get state machine statistics.
        
        Returns:
            Dictionary with statistics.
        """
        return {
            "current_state": self._current_state.value,
            "total_transitions": len(self._history),
            "valid_transitions": [s.value for s in self.get_valid_transitions()],
            "last_transition": self._history[-1].timestamp if self._history else None,
        }
