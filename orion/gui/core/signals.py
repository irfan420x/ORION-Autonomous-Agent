"""
ORION GUI Core - Global Signal Bus
===================================

Central signal bus for cross-widget communication.
"""

from PyQt6.QtCore import QObject, pyqtSignal as Signal


class SignalBus(QObject):
    """Global signal bus for inter-widget communication."""
    
    # System signals
    cpu_changed = Signal(float)
    ram_changed = Signal(float)
    disk_changed = Signal(float)
    network_changed = Signal(float, float)
    processes_updated = Signal(list)
    system_health = Signal(float)
    
    # AI signals
    ai_thinking = Signal()
    ai_response = Signal(str)
    ai_error = Signal(str)
    ai_tool_call = Signal(str, dict)
    ai_tool_result = Signal(str, str)
    
    # Voice signals
    voice_listening = Signal(bool)
    voice_level = Signal(float)
    voice_transcript = Signal(str)
    
    # Navigation signals
    page_changed = Signal(str)
    
    # Window signals
    window_minimize = Signal()
    window_restore = Signal()
    window_close = Signal()
    toggle_floating = Signal()
    toggle_lock = Signal()
    
    # Task signals
    task_added = Signal(dict)
    task_updated = Signal(dict)
    task_completed = Signal(str)
    tasks_refreshed = Signal(list)
    
    # Memory signals
    memory_stored = Signal(str, str)
    memory_recalled = Signal(str, str)
    memory_stats = Signal(dict)
    
    # Message signals
    user_message = Signal(str)
    bot_message = Signal(str)
    
    # Boot signals
    boot_progress = Signal(int, str)
    boot_complete = Signal()


# Singleton instance
_bus = None

def get_signal_bus() -> SignalBus:
    """Get the global signal bus singleton."""
    global _bus
    if _bus is None:
        _bus = SignalBus()
    return _bus
