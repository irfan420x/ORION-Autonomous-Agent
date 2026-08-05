# ORION — Autonomous Adaptive OS Agent

**Author:** IRFAN | **Version:** 2.0 | **Architecture:** Polyglot (Python + Rust + Tauri + React/TypeScript)

---

## What is ORION?

ORION is a production-grade, adaptive, self-healing Autonomous OS Agent. It understands its environment, adapts to hardware resources, responds to voice commands, can be controlled remotely, and learns from its mistakes.

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | Python 3.13+, FastAPI, Pydantic, asyncio |
| Performance | Rust (Tokio, notify, sysinfo) |
| Desktop GUI | Tauri v2 + React + TypeScript + TailwindCSS |
| Storage | SQLite + ChromaDB/Qdrant + Redis (optional) |
| Voice | faster-whisper, Kokoro/Piper, Porcupine |
| Browser | Playwright |
| Remote | Telegram Bot, REST API, WebSocket |

## For AI Agents (Claude Code / Codex)

If you are an AI agent tasked with building this project:

1. **Read `CLAUDE.md` first** — it is your Engineering Constitution.
2. **Follow the Build Order** — Phase 1 → Phase 7, no skipping.
3. **Read `state/project_state.json`** — to know where you are.
4. **Read `state/task_queue.json`** — to know what to do next.

## Project Structure

```
orion-project/
├── orion/              # Python AI Engine (Main)
├── orion-rs/           # Rust Performance Layer
├── orion-desktop/      # Tauri Desktop App (Jarvis UX)
├── config/             # YAML configuration files
├── state/              # Runtime state (JSON)
├── tests/              # Unit, Integration, E2E tests
├── docs/               # ADRs and diagrams
├── plugins/            # Third-party plugins
├── CLAUDE.md           # Engineering Constitution
├── SYSTEM_PROMPT.md    # AI Agent system prompt
├── ROADMAP.md          # Development progress
└── PROJECT_RULES.json  # Machine-readable rules
```

## License

MIT — Built by IRFAN.
