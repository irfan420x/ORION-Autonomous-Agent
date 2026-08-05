# 🚀 SESSION START INSTRUCTIONS 🚀

**ATTENTION AI AGENT (Claude Code / Codex / Cursor):**
Read this file immediately when a new coding session begins. Do not write any code until you have read this and understood the current context.

---

## 📍 Current Status
- **Target Phase:** Phase 1 (Core Foundation)
- **Target Milestone:** M1.5 (Self-Healing Architecture) — NEXT
- **Previous Milestone:** M1.4 (Adaptive Runtime) ✅ COMPLETE
- **Overall Completion:** 40%

## ✅ What Was Completed (M1.1 – M1.4)

### M1.1: Event Bus & Registry ✅
- EventBus: async pub/sub, wildcards, error isolation, history, 1000 msgs/sec
- AgentRegistry: registration, heartbeat, discovery, health tracking

### M1.2: State Machine & Task Queue ✅
- StateMachine: IDLE/PROCESSING/PAUSED/ERROR/SHUTDOWN, transitions, callbacks
- TaskQueueEngine: priority ordering, dependencies, JSON persistence, crash recovery

### M1.3: 4-Tier Memory Architecture ✅
- SessionMemory: LRU eviction, TTL, tags
- LongTermMemory: SQLite + FTS5 search
- EpisodicMemory: experience logging, pattern recognition
- SemanticMemory: vector search, mock embeddings
- MemoryManager: unified interface

### M1.4: Adaptive Runtime ✅ (NEW)
- **AdaptiveRuntime** (`orion/core/runtime/runtime.py`)
  - Hardware detection: CPU, RAM, disk, GPU, internet
  - 6 operating modes: full, cpu_only, low_memory, offline, server, safe
  - Automatic mode negotiation based on hardware
  - Continuous resource monitoring with threshold alerts
  - Auto-switch to low_memory on RAM critical
  - Module priority management (critical/high/medium/low)
  - Event publishing for all state changes
- **Telegram commands:** /runtime, /resources, /modules, /setmode

### Telegram Bot ✅
- Full control: state, tasks, memory, events, runtime commands

### Tests ✅
- 126 unit tests (all passing)
- Stability check green

## 🛠️ Instructions for Today's Session:
1. Review `BUILD_GUIDE.md` to remind yourself of the engineering rules.
2. Check `PROGRESS_TRACKER.md` to see what was completed.
3. Your immediate goal is to create the **Self-Healing Architecture**.
4. Implement `orion/reliability/health_monitor.py` (periodic health checks)
5. Implement `orion/reliability/self_healer.py` (auto-recovery protocols)
6. Write the corresponding tests in `tests/reliability/`.
7. Run the tests. If they pass, run `./scripts/stability_check.sh`.
8. **IMPORTANT:** Update Telegram bot with health commands after implementation.

## 🛑 Constraints & Reminders:
- **DO NOT** try to build the LLM Router or Vision system today. Stick to Self-Healing.
- **DO NOT** use external databases yet.
- Ensure all code is typed (`typing` module) and documented (docstrings).
- The EventBus and StateMachine are ready — use them for all inter-module communication.
- Update Telegram bot with new commands for each feature you build.

## 📁 Key Files to Review:
- `orion/core/runtime/runtime.py` — AdaptiveRuntime implementation
- `orion/core/communication/event_bus.py` — EventBus implementation
- `orion/core/state/state_machine.py` — StateMachine implementation
- `orion/remote_control/telegram_bot.py` — Telegram bot (add new commands here)
- `tests/runtime/test_runtime.py` — Example of how to write tests

---
*Note: Update this file at the end of your session so the next agent knows where to pick up.*
