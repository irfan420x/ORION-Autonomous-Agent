# ORION Master Build Guide (For AI Agents)
**Author:** IRFAN | **Version:** 1.0 | **Target Audience:** Claude Code, Codex, Cursor, Cline

**WARNING TO AI AGENT:** DO NOT attempt to build everything at once. This is a massive, production-grade Autonomous OS Agent. You must build it **incrementally**, session by session, keeping the grand vision in mind but focusing ONLY on the immediate milestone.

---

## 1. The Grand Vision (Keep this in mind)
ORION is a Polyglot (Python + Rust + Tauri) Autonomous OS Agent. It features a 4-tier memory, 6-graph world model, adaptive runtime, dynamic cost management, and a desktop GUI (Jarvis UX). Everything communicates via an Event Bus.

**Your Goal:** Build a stable, scalable, and self-healing system. Do not hardcode configurations; always use the `config/` YAML files. Do not build tightly coupled modules; always use the Event Bus.

---

## 2. Daily Session Workflow (Strict Adherence Required)

Every time a user starts a new coding session with you, you **MUST** follow this exact sequence:

### Step 1: Context Loading (First 2 minutes)
1. Read `SESSION_START.md` (This tells you exactly what to do first).
2. Read `PROGRESS_TRACKER.md` (To know what was finished yesterday and what is next today).
3. Read the relevant section of `ROADMAP.md` and `CLAUDE.md` for the current milestone.

### Step 2: Goal Alignment
1. State your understanding of today's specific goal to the user.
2. Ask the user for confirmation before writing any code.

### Step 3: Incremental Implementation
1. Write code **only** for the current milestone.
2. If you need a component from a future phase (e.g., you need the LLM Router but you are in Phase 1), **mock it** or use a simple placeholder. DO NOT jump to Phase 3.
3. Update unit tests for the code you just wrote.

### Step 4: Stability Check (Mandatory before ending session)
1. Run the test suite for the current module (`pytest tests/module_name`).
2. Run the global stability check script (`./scripts/stability_check.sh`).
3. Ensure no regressions were introduced. The system MUST compile and run, even if features are missing.

### Step 5: Session Wrap-up
1. Update `PROGRESS_TRACKER.md` with what was accomplished today.
2. Update `SESSION_START.md` with instructions for the *next* session (or for the next AI agent).
3. Commit changes to Git with a descriptive message.

---

## 3. Engineering Rules for Incremental Building

### Rule 1: "Make it Work, Make it Right, Make it Fast"
In the early phases, focus on getting the core logic working. Do not spend hours optimizing performance in Phase 1. Rust optimization comes later.

### Rule 2: The Event Bus is Sacred
If Module A needs to talk to Module B, they must NOT import each other directly if they belong to different domains. They must publish and subscribe to events on the Event Bus.

### Rule 3: Graceful Degradation
If a component fails, the system must not crash. Use `try-except` blocks, log the error using the Observability module, and return a safe fallback value.

### Rule 4: Test-Driven Increments
Do not write 500 lines of code and then test. Write 50 lines, write the test, run the test.

---

## 4. How to Handle "I'm Stuck"
If you encounter a persistent error (e.g., dependency conflicts, Rust/Python bridge issues):
1. Stop trying the same solution.
2. Document the error in `docs/KNOWN_ISSUES.md`.
3. Create a minimal reproducible example.
4. Ask the user for guidance or suggest pivoting to a different module while the issue is resolved.
