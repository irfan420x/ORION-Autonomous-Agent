# 🚀 SESSION START INSTRUCTIONS 🚀

**ATTENTION AI AGENT (Claude Code / Codex / Cursor):**
Read this file immediately when a new coding session begins. Do not write any code until you have read this and understood the current context.

---

## 📍 Current Status
- **Target Phase:** Phase 1 (Core Foundation)
- **Target Milestone:** M1.4 (Adaptive Runtime)
- **Previous Milestone:** M1.3 (4-Tier Memory Architecture) ✅ COMPLETE
- **Overall Completion:** 30%

## ✅ What Was Completed (M1.1, M1.2 & M1.3)

### M1.1: Event Bus & Registry ✅
- **EventBus** (`orion/core/communication/event_bus.py`)
  - Async pub/sub with asyncio
  - Wildcard subscriptions (e.g., `agent.*`)
  - Error isolation (failed handlers don't crash the bus)
  - Event history for debugging
  - Performance: 1000 msgs/sec verified
- **AgentRegistry** (`orion/core/communication/registry.py`)
  - Agent registration with capabilities
  - Heartbeat monitoring
  - Agent discovery by capability
  - Health status tracking

### M1.2: State Machine & Task Queue ✅
- **StateMachine** (`orion/core/state/state_machine.py`)
  - Finite state machine (IDLE, PROCESSING, PAUSED, ERROR, SHUTDOWN)
  - Valid transition guards
  - Enter/exit callbacks
  - Transition history
- **TaskQueueEngine** (`orion/core/state/task_queue.py`)
  - Priority-based task ordering
  - Dependency resolution
  - JSON file persistence (crash recovery)
  - Event publishing on task state changes

### M1.3: 4-Tier Memory Architecture ✅
- **SessionMemory** (`orion/memory/session_memory.py`) — LRU eviction, TTL, tags
- **LongTermMemory** (`orion/memory/long_term_memory.py`) — SQLite + FTS5 search
- **EpisodicMemory** (`orion/memory/episodic_memory.py`) — Experience logging, pattern recognition
- **SemanticMemory** (`orion/memory/semantic_memory.py`) — Vector search, mock embeddings
- **MemoryManager** (`orion/memory/memory_manager.py`) — Unified interface

### Telegram Bot ✅
- **Full control via Telegram** (`orion/remote_control/telegram_bot.py`)
  - State Machine commands: `/state`, `/transitions`, `/setstate`
  - Task Queue commands: `/tasks`, `/addtask`, `/completetask`, `/failedtask`
  - EventBus commands: `/events`, `/stats`
  - Memory commands: `/memory`, `/remember`, `/recall`, `/forget`, `/searchmemory`
  - System commands: `/status`, `/ping`, `/help`

### Tests ✅
- 84 unit tests (all passing)
- Performance: 1000 msgs/sec throughput
- Crash recovery verified

## 🔧 Known Issues (Fixed 2026-08-05)
- ✅ Mutable defaults (`Field([])` / `Field({})`) fixed in 21 contract files → now uses `default_factory`
- ✅ Demo files fixed: PYTHONPATH, correct API usage, enum states
- ✅ Context Engine & World Model demos marked as "requires future implementation"
- ⚠️ `pyproject.toml` says `>=3.11` but code uses Python 3.13+ features — align before release

## 🛠️ Instructions for Today's Session:
1. Review `BUILD_GUIDE.md` to remind yourself of the engineering rules.
2. Check `PROGRESS_TRACKER.md` to see what was completed.
3. Your immediate goal is to create the **Adaptive Runtime Core**.
4. Implement `orion/core/runtime/runtime.py` (Resource detection, dynamic module loading)
5. Implement resource monitoring (CPU, RAM, disk)
6. Write the corresponding tests in `tests/runtime/`.
7. Run the tests. If they pass, run `./scripts/stability_check.sh`.
8. **IMPORTANT:** Update Telegram bot with runtime commands after implementation.

## 🛑 Constraints & Reminders:
- **DO NOT** try to build the LLM Router or Vision system today. Stick to Adaptive Runtime.
- **DO NOT** use external databases yet.
- Ensure all code is typed (`typing` module) and documented (docstrings).
- The EventBus and StateMachine are ready — use them for all inter-module communication.
- Update Telegram bot with new commands for each feature you build.

## 📁 Key Files to Review:
- `orion/core/communication/event_bus.py` — EventBus implementation
- `orion/core/state/state_machine.py` — StateMachine implementation
- `orion/core/state/task_queue.py` — TaskQueueEngine implementation
- `orion/remote_control/telegram_bot.py` — Telegram bot (add new commands here)
- `tests/core/test_state_machine.py` — Example of how to write tests

---
*Note: Update this file at the end of your session so the next agent knows where to pick up.*
