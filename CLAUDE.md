# ORION: Autonomous Adaptive OS Agent (v3.0)
## Complete Engineering Constitution & Architecture Specification
**Author:** IRFAN | **Architecture:** Polyglot (Python + Rust + Tauri + React/TypeScript)
**Target AI Agents:** Claude Code, Codex, Cursor

---

## ১. AI Agent-এর জন্য সবচেয়ে গুরুত্বপূর্ণ নির্দেশ

> **এই ফাইলটি পড়ার পর আপনি ORION প্রজেক্টের Lead Systems Architect। Section 5 (Build Order) কঠোরভাবে অনুসরণ করুন। Phase 1 সম্পূর্ণ না হলে Phase 2 শুরু করবেন না। প্রতিটি Phase শেষে Verification Checklist মেলান। কোনো অনুমান করবেন না।**

---

## ২. প্রজেক্ট মিশন ও ভিশন

ORION একটি **Adaptive, Self-Healing, User-Controlled** Autonomous OS Agent। এটি শুধু কমান্ড রান করে না — এটি তার পরিবেশ বোঝে, নিজের রিসোর্স অনুযায়ী কাজ করে, ভয়েসে সাড়া দেয়, দূর থেকে নিয়ন্ত্রিত হয়, এবং নিজের ভুল থেকে শেখে।

| লক্ষ্য | বিবরণ |
|---|---|
| Adaptive Runtime | হার্ডওয়্যার অনুযায়ী নিজেকে অপ্টিমাইজ করা |
| World Model | ফাইল, প্রসেস, নেটওয়ার্কের গ্রাফ বোঝা |
| Multi-Agent | বিশেষায়িত এজেন্টদের মাধ্যমে কাজ ভাগ করা |
| Jarvis UX | ভয়েস-ফার্স্ট ডেস্কটপ অ্যাসিস্ট্যান্ট |
| Remote Control | Telegram ও REST API দিয়ে দূর থেকে নিয়ন্ত্রণ |
| Learning | ভুল ও সাফল্য থেকে শেখা |
| User-Controlled Permission | ব্যবহারকারীর নির্দেশই চূড়ান্ত, কোনো লুকানো পলিসি নেই |

---

## ৩. Polyglot Tech Stack (২০২৬)

ORION একটি Polyglot Architecture ব্যবহার করে।

### ৩.১ Language & Framework Choices

| অংশ | ভাষা/ফ্রেমওয়ার্ক | কারণ |
|---|---|---|
| AI Engine / Core Intelligence | Python 3.13+ | AI ecosystem, LLM, automation, MCP, LangGraph |
| High-Performance Services | Rust | Speed, memory safety, background services, low CPU usage |
| Desktop GUI Shell | Tauri v2 (Rust + React) | Electron-এর তুলনায় অনেক কম RAM/CPU, native feel |
| GUI Frontend | React + TypeScript + TailwindCSS | Professional UI, maintainable |
| API / Dashboard | FastAPI (Python) | Async, AI-এর সাথে ভালো integration |
| Background Workers | Python (asyncio) | AI task orchestration |
| Mobile App (Future) | Flutter | Android + iOS একসাথে |

### ৩.২ Storage Stack

| উপাদান | টেকনোলজি | উদ্দেশ্য |
|---|---|---|
| Local State | SQLite | project_state, task_queue, episodic memory |
| Vector Memory | Qdrant (self-hosted) / ChromaDB | Semantic memory, knowledge retrieval |
| Cache | Redis (optional) | Hot data, session cache |

---

## ৪. The 25 Architectural Specifications (The Brain of ORION)

এই সেকশনটি ORION-এর ২৫টি কোর ইঞ্জিন ও আর্কিটেকচার বর্ণনা করে।

### ৪.১ Agent Communication Protocol
এজেন্টরা কখনো সরাসরি একে অপরকে কল করবে না। সব যোগাযোগ হবে Event Bus-এর মাধ্যমে।
- **Agent Discovery:** বুট হওয়ার সময় এজেন্টরা Event Bus-এ নিজেদের রেজিস্টার করে।
- **Agent Registry:** কোন এজেন্ট কী কাজ করতে পারে তার ডিরেক্টরি।
- **Agent Heartbeat:** প্রতি ৫ সেকেন্ডে এজেন্টরা তাদের Health স্ট্যাটাস পাঠায়।
- **Agent Locking:** একই ফাইলে দুজন এজেন্ট যেন কাজ না করে তার জন্য Distributed Lock।
- **Agent Retry & Cancellation:** টাস্ক ফেইল করলে Retry এবং ব্যবহারকারী থামালে Cancellation প্রোটোকল।

### ৪.২ Workflow Engine
বড় অটোমেশন পরিচালনার জন্য একটি ডাইরেক্টেড অ্যাসাইক্লিক গ্রাফ (DAG) ইঞ্জিন।
`Goal → Task Graph → Workflow → Checkpoint → Resume → Complete`
টাস্কের মাঝে সিস্টেম রিস্টার্ট হলেও Checkpoint থেকে আবার শুরু হবে।

### ৪.৩ Skill System
ORION শুধু টুল চালায় না, তার Skill আছে।
- **Reusable Skills:** `Create Website`, `Research Topic`, `Deploy App`, `Write Report`।
- **Skill Execution:** একটি স্কিল একাধিক টুলের সমন্বয়ে গঠিত একটি ওয়ার্কফ্লো।

### ৪.৪ Plugin SDK & Architecture
থার্ড-পার্টি এক্সটেনশনের জন্য সিকিউর আর্কিটেকচার।
- **Plugin Manifest:** JSON ফাইল যা প্লাগিনের নাম, ভার্সন ও পারমিশন সংজ্ঞায়িত করে।
- **Plugin Sandbox:** প্লাগিনগুলো изолиিত (isolated) পরিবেশে চলবে।
- **Plugin Permission:** প্লাগিন কোর সিস্টেমে অ্যাক্সেস পাবে না, শুধু অনুমোদিত API ব্যবহার করবে।

### ৪.৫ Self-Healing Architecture
সিস্টেম নিজে নিজেকে মেরামত করবে।
- **Health Monitor:** প্রতি মিনিটে কোর সার্ভিসগুলোর হেলথ চেক।
- **Corruption Detection:** ডাটাবেস বা কনফিগ ফাইল নষ্ট হলে স্বয়ংক্রিয়ভাবে ব্যাকআপ থেকে রিস্টোর।
- **Dependency Repair:** কোনো লাইব্রেরি মুছে গেলে নিজে থেকে `pip` বা `cargo` দিয়ে ইন্সটল।

### ৪.৬ Observability (Production-Grade)
- **Metrics:** Prometheus ব্যবহার করে CPU, RAM, Agent Health ট্র্যাক।
- **Tracing:** OpenTelemetry দিয়ে টাস্কের শুরু থেকে শেষ পর্যন্ত ট্র্যাকিং।
- **Token & Cost Usage:** প্রতিটি LLM কলের খরচ এবং টোকেন হিসাব করে ড্যাশবোর্ডে দেখানো।

### ৪.৭ Vision Architecture
`Vision Engine → OCR → UI Detection → Grounding → Object Detection → Reasoning`
শুধু স্ক্রিনশট নেওয়া নয়, স্ক্রিনের প্রতিটি উপাদানের bounding box বের করে তার উপর লজিক খাটানো।

### ৪.৮ GUI Automation Architecture
- **Accessibility API:** Windows/Linux-এর নেটিভ API (AT-SPI2) ব্যবহার করে UI পড়া।
- **Mouse/Keyboard:** `pyautogui` বা Rust-এর `enigo` ব্যবহার করে হিউম্যান-লাইক মাউস মুভমেন্ট ও কীবোর্ড শর্টকাট।

### ৪.৯ Browser Architecture (Playwright)
- **Browser Manager:** সেশন, প্রোফাইল, কুকিজ এবং ট্যাব পরিচালনা।
- **Human Takeover:** ব্রাউজার অটোমেশনের সময় ক্যাপচা এলে বা এজেন্ট আটকে গেলে সিস্টেম পজ হয়ে ব্যবহারকারীকে Takeover করার সুযোগ দেবে।

### ৪.১০ Security Architecture
- **User-Controlled Permission Model:** ব্যবহারকারী ঠিক করবে কোন টুলে `ALLOW`, `CONFIRM_USER`, বা `DENY` থাকবে।
- **Secrets Vault:** API-Key গুলো এনক্রিপ্টেড অবস্থায় থাকবে।
- **Audit Logs:** প্রতিটি সেনসিটিভ কাজের রেকর্ড রাখা হবে।

### ৪.১১ Learning Engine
- **Failure Learning:** ভুল হলে সমাধানটি `Error Memory`-তে সেভ হবে।
- **Prompt Learning:** কোন প্রম্পটে ভালো উত্তর আসে তা শিখে অপ্টিমাইজ করা।
- **Workflow Learning:** ব্যবহারকারীর প্রতিদিনের কাজের প্যাটার্ন শিখে টেমপ্লেট তৈরি।

### ৪.১২ Knowledge Engine
- **Knowledge Graph:** তথ্যের মধ্যে সম্পর্ক তৈরি।
- **Document Indexing:** ফোল্ডারের সব PDF/Word ফাইল ভেক্টর ডাটাবেসে ইনডেক্স করা।

### ৪.১৩ Dependency Engine
- **Auto Install:** টাস্কের জন্য কোনো টুল (যেমন `ffmpeg`) না থাকলে নিজে ইন্সটল করা।
- **Version Check:** টুলের সঠিক ভার্সন আছে কিনা যাচাই করা।

### ৪.১৪ Adaptive Runtime (Capability Negotiation)
- **Startup Detection:** বুট হওয়ার সময় হার্ডওয়্যার স্ক্যান।
- **Dynamic Module Loading:** RAM কম থাকলে ভারী মডিউলগুলো (যেমন Local LLM) আনলোড করে Cloud API-তে সুইচ করা।
- **Resource Budgeting:** CPU যেন ১০০% ব্যবহার না হয় তার জন্য থ্রটলিং (Throttling)।

### ৪.১৫ Desktop GUI Architecture (Jarvis UX)
- **Desktop Overlay:** স্ক্রিনের এক কোণায় ভাসমান (Floating Orb) অ্যাসিস্ট্যান্ট।
- **Live Task Panel:** বর্তমানে কী কাজ চলছে তার লাইভ স্ট্যাটাস।
- **Voice Animation:** কথা বলার সময় অডিও ভিজ্যুয়ালাইজার।

### ৪.১৬ Mobile Architecture & Multi-device Sync
- **Future Flutter App:** মোবাইল থেকে পিসির এজেন্টকে নিয়ন্ত্রণ।
- **Multi-device Sync:** ল্যাপটপ এবং ডেস্কটপের মধ্যে `state` সিঙ্ক করা (Cloud/Local Network-এর মাধ্যমে)।

### ৪.১৭ Distributed Architecture (Future)
- **Cluster Support:** একাধিক মেশিনে কাজ ভাগ করে দেওয়া (যেমন একটি পিসি ব্রাউজ করবে, অন্যটি মডেল রান করবে)।

### ৪.১৮ Context Engine
- **History Compression:** অনেক বড় চ্যাট হিস্ট্রি হলে তা সামারাইজ করে টোকেন বাঁচানো।
- **Workspace Context:** বর্তমান খোলা ফোল্ডার বা ফাইলের কন্টেক্সট সবসময় মনে রাখা।

### ৪.১৯ Execution Policy (Decision Matrix)
- **CPU-only:** Small Model → No Vision → Cloud OCR
- **GPU-enabled:** Large Local Model → Parallel Vision → Fast Response

### ৪.২০ Human Takeover Protocol
এজেন্ট আটকে গেলে: `Pause Task → Notify User → User Takes Action → Agent Resumes`।

### ৪.২১ Recovery Matrix
Failure Matrix-এর পাশাপাশি প্রতিটি ভুলের জন্য সুনির্দিষ্ট Recovery Protocol (যেমন: Network error → Exponential Backoff)।

### ৪.২২ Cost Manager
- **Monthly Budget:** ব্যবহারকারী বাজেট সেট করবে।
- **Dynamic Routing:** বাজেট শেষের দিকে হলে Cloud LLM থেকে Local LLM-এ সুইচ করবে।

### ৪.২৩ Developer Toolkit
- **Debug Console:** রিয়েল-টাইম লগ দেখার প্যানেল।
- **Memory & Task Viewer:** ডাটাবেস এবং DAG ভিজ্যুয়ালাইজ করার টুল।

### ৪.২৪ Testing Architecture
- **Unit & Integration:** সব কোডের টেস্ট।
- **Performance & Stress:** সিস্টেম ১০০% লোডে কেমন আচরণ করে তার টেস্ট।

### ৪.২৫ Context Window Management
LLM-এর টোকেন লিমিট যেন পার না হয়, তার জন্য স্লাইডিং উইন্ডো এবং RAG (Retrieval-Augmented Generation) ব্যবহার।

---

## ৫. Project Structure & Engineering Rules

ORION uses a **Nested Architectural Pattern**. Each major subsystem contains its own `CLAUDE.md` for localized context.

### ৫.১ Detailed Directory Layout (The ORION Matrix)

```text
ORION-master/
├── CLAUDE.md                   # Root Engineering Constitution (Master Guide)
├── ROADMAP.md                  # High-level Milestone & Test Gate Tracker
├── SYSTEM_PROMPT.md            # Core Instructions for the AI Agent
├── PROJECT_RULES.json          # Machine-readable Constraints & Safety
├── pyproject.toml              # Global Python Dependencies & Build Config
├── BUILD_GUIDE.md              # Incremental Build Instructions
├── PROGRESS_TRACKER.md         # Daily Session Tracking
├── SESSION_START.md            # Entry point for every new AI session
├── config/                     # Multi-layer YAML Configuration
│   ├── system.yaml             # Core Engine & Operating Modes
│   ├── model.yaml              # LLM Routing & Fallback Policies
│   ├── permission_config.yaml  # User-Controlled Permission Rules
│   ├── tool_config.yaml        # Tool Discovery & Health Checks
│   ├── voice.yaml              # STT/TTS & Audio Processing
│   ├── telegram.yaml           # Remote Control Auth & Roles
│   └── failure_matrix.yaml     # Recovery State Machine Protocols
├── docs/                       # Project Documentation
│   ├── adr/                    # Architecture Decision Records (ADRs)
│   └── diagrams/               # Architecture & Flow Diagrams
├── examples/                   # Subsystem Demo & Integration Scripts
│   ├── event_bus_demo.py
│   ├── state_task_queue_demo.py
│   ├── memory_demo.py
│   ├── context_engine_demo.py
│   └── world_model_demo.py
├── orion/                      # Python Core (Nested Subsystems)
│   ├── contracts/              # Pydantic Models & Event Schemas (Contracts-First)
│   │   ├── agent_contracts.py
│   │   ├── memory_contracts.py
│   │   ├── vision_contracts.py
│   │   └── [22 more contract files...]
│   ├── core/                   # The Nervous System
│   │   ├── communication/      # Event Bus & Agent Registry (Nested CLAUDE.md)
│   │   ├── runtime/            # Adaptive Engine (Nested CLAUDE.md)
│   │   └── state/              # State Machine & Task Queue (Nested CLAUDE.md)
│   ├── intelligence/           # The Prefrontal Cortex
│   │   ├── planning/           # DAG Planning Engine (Nested CLAUDE.md)
│   │   ├── policy/             # Execution Decision Matrix (Nested CLAUDE.md)
│   │   ├── router/             # Model Routing & Cost Optimization
│   │   └── reasoning/          # Reflection & Verification
│   ├── environment/            # Sensory & Actuator Interfaces
│   │   ├── os/                 # System Control (Terminal/Files)
│   │   ├── gui/                # Accessibility-based Automation
│   │   ├── browser/            # Playwright-based Intelligence
│   │   └── vision/             # OCR & Visual Grounding
│   ├── [15 more subsystems...] # Memory, Learning, Security, etc. (Nested CLAUDE.md)
├── orion-rs/                   # Rust Performance Layer (Process/File Watchers)
├── orion-desktop/              # Tauri Desktop Shell (React + TypeScript)
└── scripts/                    # Stability & Verification Tools
    └── stability_check.sh      # Mandatory Session-End Verification Script
```

### ৫.২ Engineering Rules
- **Contracts-First:** Define Pydantic models in `orion/contracts/` BEFORE implementing logic.
- **Nested Context:** Always read the local `CLAUDE.md` before working in a subsystem.
- **Language Choice:** Python for AI/Automation, Rust for System/Performance, TS/React for UI.
- **Async-First:** All Python code must be asynchronous (asyncio).
- **Type Safety:** Strict type hinting in Python, TypeScript for Frontend.
- **Verification:** Every session must end with running `./scripts/stability_check.sh`.
- **Safety:** Follow User-Controlled Permission Model strictly.

---

## ৬. Build Order: Step-by-Step Implementation Guide

> **AI Agent: এই ক্রম ভাঙা কঠোরভাবে নিষিদ্ধ। Phase 1 শেষ না করে Phase 2 শুরু করবেন না।**

### Phase 1: Core Foundation & Communication (Python)
- Adaptive Runtime Core (`runtime.py`)
- Agent Communication Protocol (Event Bus, Registry, Heartbeat)
- State Machine & Task Queue Engine
- 4-Tier Memory Architecture (Session, Long-term, Episodic, Semantic)
- Context Engine (Compression, Window Management)

### Phase 2: World Model, Resource & Dependency (Python + Rust)
- Hardware Detector & Capability Negotiation (Adaptive Runtime)
- Dependency Engine (Auto Install, Version Check)
- Workspace, Process, Network, File, Git, Window Graphs
- Rust Process Monitor & File Watcher (`orion-rs/`)

### Phase 3: Intelligence, Model & Cost Management (Python)
- Goal Manager & Planning Engine (DAG)
- Execution Policy (Decision Matrix)
- Model Router & Cost Manager (Budgeting, Dynamic Routing)
- Reasoning, Reflection & Verification Engines
- Local (Ollama) & Cloud (Claude/GPT) Model Clients

### Phase 4: Multi-Agent System, Skills & Plugins (Python)
- Base Agent & Core Agents (Planner, Executor, Browser, Vision, etc.)
- Skill System (Reusable Workflows)
- Plugin SDK (Manifest, Sandbox, Permissions)
- Tool Registry & User-Controlled Permission Model

### Phase 5: Environment Control, GUI & Browser (Python + Rust)
- OS Control (Terminal, Filesystem, Process, Window)
- GUI Automation Architecture (Accessibility API, Mouse/Keyboard)
- Browser Architecture (Playwright Manager, Profiles, Human Takeover)
- Vision Architecture (OCR, UI Detection, Grounding)

### Phase 6: Voice, Remote Control & Jarvis UX (Python + Tauri + React)
- Voice System (Wake Word, STT, TTS, Interrupt)
- Remote Control (Telegram, REST API, WebSocket)
- Desktop GUI Architecture (Tauri Shell, Overlay, Floating Orb, Task Panel)
- Security Architecture (Secrets Vault, Encryption, Audit Logs)

### Phase 7: Autonomy, Learning, Reliability & DevTools (Python + Rust)
- Autonomous Watchers & Scheduler
- Learning Engine (Failure, Prompt, Workflow Learning)
- Knowledge Engine (Graph, Document Indexing)
- Self-Healing Architecture & Recovery Matrix
- Observability (Metrics, Tracing) & Developer Toolkit (Debug Console, Viewers)
- Testing Architecture (Unit, E2E, Stress)

---

## ৬. Absolute Rules (অলঙ্ঘনীয় নিয়ম)

| Rule ID | নিয়ম | অগ্রাধিকার |
|---|---|---|
| RULE-ABS-001 | User-Controlled Permission: ব্যবহারকারীর নির্দেশই চূড়ান্ত | Critical |
| RULE-ABS-002 | No Assumptions: বুঝতে না পারলে প্রশ্ন করো, অনুমান করো না | High |
| RULE-ABS-003 | Deterministic State: প্রতিটি কাজের আগে/পরে state আপডেট বাধ্যতামূলক | Critical |
| RULE-ABS-004 | Phase Strictness: Build Order-এর ক্রম ভাঙা যাবে না | Critical |
| RULE-ABS-005 | Polyglot Discipline: সঠিক component-এ সঠিক ভাষা (Python/Rust/Tauri) ব্যবহার | High |
| RULE-ABS-006 | Event Bus Communication: এজেন্টরা সরাসরি কল করবে না | Critical |

---

## ৭. Verification Checklist (Definition of Done)

প্রতিটি Phase শেষে এবং প্রতিটি কমিটের আগে:

- [ ] **Phase Completion:** বর্তমান Phase-এর সব Component তৈরি এবং কার্যকর।
- [ ] **State Updated:** `state/project_state.json` এবং `state/task_queue.json` আপডেট।
- [ ] **No Placeholders:** কোডে কোনো `TODO`, `pass`, বা `raise NotImplementedError` নেই।
- [ ] **Tests Written:** প্রতিটি module-এর জন্য unit test আছে।
- [ ] **Architecture Adherence:** নতুন কোড Directory Structure মেনে সঠিক ফোল্ডারে।
- [ ] **ROADMAP Updated:** `ROADMAP.md`-এ সম্পন্ন আইটেমগুলো `[x]` করা হয়েছে।

---
*ORION — Built by IRFAN. Powered by Polyglot Architecture. Guided by this Constitution.*

### ৪.১ Agent Communication Protocol (বিস্তারিত)
এজেন্টরা কখনো সরাসরি একে অপরকে কল করবে না। সব যোগাযোগ হবে Event Bus-এর মাধ্যমে। এটি একটি Pub/Sub মডেল অনুসরণ করে, যেখানে এজেন্টরা ইভেন্ট পাবলিশ করে এবং অন্যান্য এজেন্টরা তাদের আগ্রহ অনুযায়ী ইভেন্ট সাবস্ক্রাইব করে।
- **Agent Discovery & Registry:** বুট হওয়ার সময় প্রতিটি এজেন্ট `AgentRegistry` মডিউলে নিজেদের `AgentID`, `Capabilities` (যেমন: `can_browse`, `can_code`, `can_vision`), `Health Status` এবং `Endpoint` (যদি সরাসরি কমিউনিকেশন প্রয়োজন হয়) রেজিস্টার করে। `AgentRegistry` একটি SQLite ডাটাবেসে সংরক্ষিত থাকে এবং Event Bus-এর মাধ্যমে আপডেটেড থাকে।
- **Agent Heartbeat:** প্রতিটি এজেন্ট প্রতি ৫ সেকেন্ডে `agent.heartbeat` ইভেন্ট পাবলিশ করে। `AgentRegistry` এই হার্টবিট মনিটর করে এজেন্টের হেলথ স্ট্যাটাস আপডেট করে। যদি কোনো এজেন্ট নির্দিষ্ট সময় (যেমন ১৫ সেকেন্ড) হার্টবিট না পাঠায়, তাকে `UNRESPONSIVE` হিসেবে চিহ্নিত করা হয় এবং `Self-Healing Architecture` ট্রিগার হতে পারে।
- **Agent Locking:** একই রিসোর্স (যেমন একটি ফাইল, একটি ব্রাউজার সেশন) নিয়ে একাধিক এজেন্ট কাজ করা আটকাতে `DistributedLockManager` ব্যবহার করা হয়। কোনো এজেন্ট একটি রিসোর্স ব্যবহার করার আগে লক রিকোয়েস্ট করে এবং কাজ শেষে লক রিলিজ করে। এটি `Redis` বা `SQLite` ভিত্তিক হতে পারে।
- **Agent Priority & Preemption:** কিছু টাস্কের অগ্রাধিকার বেশি থাকতে পারে। `TaskQueueEngine` এজেন্টের অগ্রাধিকার অনুযায়ী টাস্ক অ্যাসাইন করে। উচ্চ অগ্রাধিকারের টাস্ক প্রয়োজনে চলমান নিম্ন অগ্রাধিকারের টাস্ককে `preempt` (সাময়িকভাবে স্থগিত) করতে পারে।
- **Agent Timeout & Retry:** প্রতিটি টাস্কের জন্য একটি নির্দিষ্ট `timeout` থাকে। যদি এজেন্ট সেই সময়ের মধ্যে কাজ শেষ করতে না পারে, `Recovery Matrix` অনুযায়ী `RETRY` বা `REPLAN` প্রোটোকল ট্রিগার হয়।
- **Agent Cancellation:** ব্যবহারকারী বা `Orchestrator` একটি চলমান টাস্ক বাতিল করতে চাইলে `agent.cancel_task` ইভেন্ট পাঠায়। এজেন্টকে এই ইভেন্ট হ্যান্ডেল করে gracefully কাজ বন্ধ করতে হয়।
- **Agent Capability Advertisement:** এজেন্টরা তাদের বর্তমান ক্ষমতা (যেমন: `GPU available`, `internet connected`, `local LLM loaded`) `AgentRegistry`-তে অ্যাডভার্টাইজ করে, যা `Adaptive Runtime` এবং `Model Router` টাস্ক অ্যাসাইনমেন্টে ব্যবহার করে।

### ৪.২ Workflow Engine (বিস্তারিত)
ORION-এর বড় অটোমেশন টাস্কগুলো `Workflow Engine` দ্বারা পরিচালিত হয়। এটি একটি `Directed Acyclic Graph (DAG)` ভিত্তিক সিস্টেম, যা জটিল টাস্কগুলোকে ছোট ছোট, নির্ভরশীল ধাপে বিভক্ত করে।
- **Goal Management:** ব্যবহারকারীর দেওয়া উচ্চ-স্তরের Goal-কে `Planning Engine` একটি `Task Graph` এ রূপান্তরিত করে।
- **Task Graph (DAG):** প্রতিটি নোড একটি `Task` এবং প্রতিটি এজ একটি `Dependency` নির্দেশ করে। টাস্কগুলো সমান্তরালভাবে বা ক্রমানুসারে এক্সিকিউট হতে পারে।
- **Workflow Execution:** `Workflow Engine` টাস্ক গ্রাফ অনুসরণ করে টাস্কগুলো `TaskQueueEngine`-এ পাঠায়। এটি টাস্কের স্ট্যাটাস মনিটর করে এবং ডিপেন্ডেন্সি পূরণ হলে পরবর্তী টাস্ক ট্রিগার করে।
- **Checkpointing & Resume:** প্রতিটি টাস্ক সফলভাবে শেষ হওয়ার পর `project_state.json`-এ একটি `checkpoint` সেভ করা হয়। সিস্টেম ক্র্যাশ করলে বা রিস্টার্ট হলে, `Workflow Engine` শেষ চেকপয়েন্ট থেকে কাজ আবার শুরু করতে পারে, পুরো ওয়ার্কফ্লো নতুন করে শুরু করার প্রয়োজন হয় না।
- **Error Handling:** `Recovery Matrix` অনুযায়ী কোনো টাস্ক ফেইল করলে `Workflow Engine` স্বয়ংক্রিয়ভাবে `RETRY`, `REPLAN` বা `ESCALATE` করে।
- **Dynamic Workflow Modification:** `Planning Engine` বা ব্যবহারকারীর নির্দেশে চলমান ওয়ার্কফ্লো ডাইনামিকভাবে পরিবর্তন করা যেতে পারে (যেমন: একটি নতুন টাস্ক যোগ করা বা একটি টাস্ক বাদ দেওয়া)।

### ৪.৩ Skill System (বিস্তারিত)
ORION শুধু লো-লেভেল টুল চালায় না, এটি উচ্চ-স্তরের `Skills` এক্সিকিউট করতে পারে। একটি `Skill` হলো একটি প্রি-ডিফাইন্ড ওয়ার্কফ্লো বা টাস্ক গ্রাফ যা একটি নির্দিষ্ট, জটিল কাজ সম্পন্ন করে।
- **Skill Definition:** প্রতিটি Skill একটি YAML বা JSON ফাইলে সংজ্ঞায়িত হয়, যেখানে তার `name`, `description`, `required_capabilities`, `input_schema`, `output_schema` এবং `underlying_workflow` (Task Graph) উল্লেখ থাকে।
- **Reusable Skills:** `Create Website`, `Research Topic`, `Deploy App`, `Create Presentation`, `Write Report`, `Analyze Code` — এই ধরনের Skill গুলোকে মডিউলার এবং পুনরায় ব্যবহারযোগ্য করে ডিজাইন করা হয়।
- **Skill Execution:** যখন ব্যবহারকারী একটি Skill রিকোয়েস্ট করে, `Planning Engine` সেই Skill-এর `underlying_workflow` লোড করে এবং `Workflow Engine`-এর মাধ্যমে এক্সিকিউট করে।
- **Skill Manifest:** একটি `skill_manifest.yaml` ফাইল থাকবে যা ORION-এর কাছে উপলব্ধ সব Skill-এর একটি তালিকা এবং তাদের মেটাডেটা ধারণ করবে।
- **Dynamic Skill Discovery:** `plugins/` ফোল্ডারে নতুন Skill ফাইল যোগ করলে ORION স্বয়ংক্রিয়ভাবে সেগুলো ডিসকভার করে `Skill Manifest`-এ যোগ করবে।
- **Skill Versioning:** Skill গুলোর ভার্সন থাকবে, যাতে আপডেটের সময় backward compatibility বজায় রাখা যায়।

### ৪.৪ Plugin SDK & Architecture (বিস্তারিত)
ORION-এর কার্যকারিতা বাড়ানোর জন্য একটি শক্তিশালী `Plugin SDK` (Software Development Kit) রয়েছে। এটি থার্ড-পার্টি ডেভেলপারদের ORION-এর কোর লজিক পরিবর্তন না করেই নতুন ফিচার, টুল বা স্কিল যোগ করার সুযোগ দেয়।
- **Plugin Manifest:** প্রতিটি প্লাগিনের একটি `plugin.yaml` ফাইল থাকবে, যা প্লাগিনের `name`, `version`, `author`, `description`, `required_capabilities`, `dependencies` এবং `entry_point` (প্লাগিনের প্রধান ফাইল) সংজ্ঞায়িত করবে।
- **Plugin Lifecycle:** প্লাগিনগুলো `load`, `activate`, `deactivate`, `unload` — এই লাইফসাইকেল ইভেন্টগুলো অনুসরণ করবে। `PluginManager` এই ইভেন্টগুলো পরিচালনা করবে।
- **Plugin API:** প্লাগিনগুলো ORION-এর কোর ফাংশনালিটি অ্যাক্সেস করার জন্য একটি সুনির্দিষ্ট API ব্যবহার করবে। এই API-এর মাধ্যমে প্লাগিনগুলো `Event Bus`-এ ইভেন্ট পাবলিশ/সাবস্ক্রাইব করতে পারবে, `Memory` অ্যাক্সেস করতে পারবে, `Tool` ব্যবহার করতে পারবে এবং নতুন `Skill` রেজিস্টার করতে পারবে।
- **Plugin Sandbox:** নিরাপত্তার জন্য প্লাগিনগুলো একটি `isolated environment` (যেমন Python-এর জন্য আলাদা ভার্চুয়াল এনভায়রনমেন্ট বা Rust-এর জন্য WebAssembly স্যান্ডবক্স) এ চলবে। এটি কোর সিস্টেমকে ম্যালিশিয়াস বা ত্রুটিপূর্ণ প্লাগিন থেকে রক্ষা করবে।
- **Plugin Dependencies:** প্লাগিনগুলো তাদের নিজস্ব Python বা Rust ডিপেন্ডেন্সি ঘোষণা করতে পারবে, যা `Dependency Engine` দ্বারা স্বয়ংক্রিয়ভাবে ইন্সটল ও ম্যানেজ হবে।
- **Plugin Permission:** প্রতিটি প্লাগিনের জন্য `User-Controlled Permission Model`-এ আলাদা পারমিশন সেট করা যাবে, যা প্লাগিনের অ্যাক্সেস কন্ট্রোল করবে।

### ৪.৫ Self-Healing Architecture (বিস্তারিত)
ORION একটি **Self-Healing** সিস্টেম, যা নিজে নিজেই ত্রুটি শনাক্ত করে এবং মেরামত করে। এটি সিস্টেমের স্থিতিশীলতা এবং নির্ভরযোগ্যতা নিশ্চিত করে।
- **Health Monitor:** `orion-rs/health_monitor` (Rust) মডিউলটি ব্যাকগ্রাউন্ডে কোর ORION সার্ভিস, এজেন্ট, এবং সিস্টেম রিসোর্স (CPU, RAM, Disk, Network) নিয়মিত মনিটর করে। এটি প্রতি মিনিটে `system.health_status` ইভেন্ট পাবলিশ করে।
- **Corruption Detection & Repair:** `DataIntegrityManager` (Python) নিয়মিত `project_state.json`, `task_queue.json`, এবং `SQLite` ডাটাবেসের ইন্টিগ্রিটি চেক করে। যদি কোনো করাপশন (corruption) ধরা পড়ে, এটি স্বয়ংক্রিয়ভাবে শেষ ভালো ব্যাকআপ থেকে রিস্টোর করার চেষ্টা করে।
- **Dependency Repair:** `Dependency Engine` (Section 4.13) কোনো মিসিং বা করাপ্টেড সিস্টেম ডিপেন্ডেন্সি (যেমন `nmap` বাইনারি) বা Python/Rust প্যাকেজ শনাক্ত করলে, `Self-Healing` প্রোটোকল স্বয়ংক্রিয়ভাবে সেটিকে পুনরায় ইন্সটল বা মেরামত করার চেষ্টা করে।
- **Auto Restart & Recovery:** যদি কোনো কোর সার্ভিস (যেমন Event Bus) ক্র্যাশ করে, `ServiceManager` (Python) সেটিকে স্বয়ংক্রিয়ভাবে রিস্টার্ট করার চেষ্টা করে। `Recovery Matrix` (Section 4.21) অনুযায়ী, রিস্টার্টের পর `Workflow Engine` শেষ চেকপয়েন্ট থেকে কাজ আবার শুরু করে।
- **Resource Management:** `Resource Awareness` (Section 4.14) মডিউলটি সিস্টেম রিসোর্স মনিটর করে। যদি কোনো রিসোর্স (যেমন RAM) সংকটপূর্ণ অবস্থায় পৌঁছায়, `Self-Healing` প্রোটোকল স্বয়ংক্রিয়ভাবে `SCALE_DOWN` (যেমন: কম মেমরি মোডে সুইচ করা, ভারী মডিউল আনলোড করা) অ্যাকশন ট্রিগার করে।

### ৪.৬ Observability (Production-Grade) (বিস্তারিত)
ORION-এর `Observability` আর্কিটেকচার সিস্টেমের অভ্যন্তরীণ অবস্থা সম্পর্কে গভীর অন্তর্দৃষ্টি প্রদান করে, যা ডিবাগিং, পারফরম্যান্স অপ্টিমাইজেশন এবং সমস্যা সমাধানে সহায়তা করে।
- **Metrics:** `Prometheus` ব্যবহার করে সিস্টেমের বিভিন্ন মেট্রিক্স (CPU usage, RAM usage, Disk I/O, Network traffic, Agent health, Task queue length, Event Bus throughput, LLM token usage, API call latency) সংগ্রহ করা হয়। `orion-rs/metrics_collector` (Rust) সিস্টেম-লেভেলের মেট্রিক্স সংগ্রহ করে এবং `orion/observability/metrics.py` (Python) অ্যাপ্লিকেশন-লেভেলের মেট্রিক্স এক্সপোজ করে।
- **Tracing:** `OpenTelemetry` ব্যবহার করে প্রতিটি টাস্কের শুরু থেকে শেষ পর্যন্ত (end-to-end) ট্রেসিং ইমপ্লিমেন্ট করা হয়। এটি একটি টাস্কের মধ্যে বিভিন্ন এজেন্ট, মডিউল এবং টুল কলের মধ্যে ডেটা ফ্লো এবং ল্যাটেন্সি ভিজ্যুয়ালাইজ করতে সাহায্য করে।
- **Structured Logging:** `structlog` ব্যবহার করে সমস্ত লগ স্ট্রাকচার্ড JSON ফরম্যাটে জেনারেট করা হয়। এতে লগ বিশ্লেষণ এবং ফিল্টারিং সহজ হয়। লগ লেভেল `config/system.yaml`-এ কনফিগার করা যায়।
- **Dashboard & Visualization:** `Grafana` (বা অনুরূপ টুল) ব্যবহার করে Prometheus মেট্রিক্স এবং OpenTelemetry ট্রেস ভিজ্যুয়ালাইজ করার জন্য কাস্টম ড্যাশবোর্ড তৈরি করা হয়। `Developer Toolkit` (Section 4.23) এর মাধ্যমে এই ড্যাশবোর্ডগুলো অ্যাক্সেস করা যায়।
- **Cost Usage Monitoring:** `Model Router` (Section 4.19) প্রতিটি LLM কলের খরচ ট্র্যাক করে এবং `Cost Manager` (Section 4.22) মাসিক বাজেট এবং খরচ মনিটর করে। এই ডেটা মেট্রিক্স সিস্টেমে পাঠানো হয়।
- **Event Timeline:** `Event Bus` থেকে প্রাপ্ত ইভেন্টগুলো একটি টাইমলাইনে ভিজ্যুয়ালাইজ করা হয়, যা সিস্টেমের ইভেন্ট ফ্লো বুঝতে সাহায্য করে।

### ৪.৭ Vision Architecture (বিস্তারিত)
ORION-এর `Vision Architecture` শুধু স্ক্রিনশট নেওয়া নয়, স্ক্রিনের প্রতিটি উপাদানের `bounding box` বের করে তার উপর লজিক খাটানো এবং ভিজ্যুয়াল ডেটা থেকে গভীর ইনসাইট বের করার ক্ষমতা রাখে।
- **Vision Engine:** এটি `OpenCV` এবং `Pillow` ব্যবহার করে ইমেজ প্রসেসিংয়ের কোর ফাংশনালিটি প্রদান করে।
- **OCR (Optical Character Recognition):** `EasyOCR` (লোকাল) বা ক্লাউড-ভিত্তিক OCR সার্ভিস (যেমন Google Vision API) ব্যবহার করে ইমেজ থেকে টেক্সট এক্সট্র্যাক্ট করা হয়। `Model Router` (Section 4.19) `vision_ocr_only` টাস্কের জন্য মডেল রাউটিং পরিচালনা করে।
- **UI Detection & Grounding:** `Ultralytics YOLO` বা অন্যান্য কম্পিউটার ভিশন মডেল ব্যবহার করে স্ক্রিনের UI উপাদান (বাটন, টেক্সট বক্স, আইকন) শনাক্ত করা হয়। `Grounding` মানে এই শনাক্তকৃত উপাদানগুলোকে তাদের অর্থপূর্ণ কনটেক্সটের সাথে সংযুক্ত করা।
- **Object Detection:** স্ক্রিনে নির্দিষ্ট অবজেক্ট (যেমন একটি ফাইল আইকন, একটি ব্রাউজার উইন্ডো) শনাক্ত করার ক্ষমতা।
- **Visual Reasoning:** `Vision LLM` (যেমন `Llava` বা `GPT-4o` ভিশন) ব্যবহার করে ভিজ্যুয়াল ডেটা থেকে উচ্চ-স্তরের ইনসাইট (যেমন: "এই স্ক্রিনশটে কী ঘটছে?", "ব্যবহারকারী কী করতে চাইছে?") বের করা হয়।
- **Vision Fallback Policy:** `config/model.yaml`-এ সংজ্ঞায়িত `vision_fallback` পলিসি অনুযায়ী, GPU না থাকলে, অফলাইন মোডে থাকলে বা লো-মেমরি অবস্থায় থাকলে স্বয়ংক্রিয়ভাবে ক্লাউড OCR বা ভিশন ডিজেবল করা হয়।

### ৪.৮ GUI Automation Architecture (বিস্তারিত)
ORION-এর `GUI Automation Architecture` অপারেটিং সিস্টেমের গ্রাফিক্যাল ইউজার ইন্টারফেসের সাথে ইন্টারঅ্যাক্ট করার ক্ষমতা প্রদান করে, যা ব্যবহারকারীর কাজ স্বয়ংক্রিয় করতে অপরিহার্য।
- **Accessibility API Integration:** Windows-এর জন্য `UI Automation` এবং Linux-এর জন্য `AT-SPI2` (Accessibility Toolkit Service Provider Interface) ব্যবহার করে ORION UI উপাদানগুলো (যেমন বাটন, টেক্সট ফিল্ড, উইন্ডো) প্রোগ্রাম্যাটিকভাবে শনাক্ত করতে, তাদের প্রপার্টি পড়তে এবং তাদের সাথে ইন্টারঅ্যাক্ট করতে পারে। এটি `Vision Architecture` (Section 4.7) এর `UI Detection` এর সাথে সমন্বয় করে কাজ করে।
- **Mouse & Keyboard Emulation:** `pyautogui` (Python) বা Rust-এর `enigo` লাইব্রেরি ব্যবহার করে ORION মাউস মুভমেন্ট, ক্লিক, স্ক্রল এবং কীবোর্ড ইনপুট (টাইপিং, হটকি) অনুকরণ করতে পারে। এটি হিউম্যান-লাইক ইন্টারঅ্যাকশন প্যাটার্ন ফলো করে, যাতে অটোমেশন স্বাভাবিক মনে হয়।
- **Window Management:** ORION উইন্ডো খুলতে, বন্ধ করতে, রিসাইজ করতে, মুভ করতে এবং ফোকাস পরিবর্তন করতে পারে। এটি `World Model` (Section 4.18) এর `Window Graph` এর সাথে সমন্বয় করে কাজ করে।
- **Cross-Platform Compatibility:** `Tauri` ফ্রেমওয়ার্কের মাধ্যমে ORION Windows, Linux এবং macOS-এ GUI অটোমেশন সমর্থন করে, তবে নেটিভ Accessibility API-এর ভিন্নতার কারণে কিছু প্ল্যাটফর্ম-নির্দিষ্ট ইমপ্লিমেন্টেশন প্রয়োজন হতে পারে।
- **Event Injection:** সরাসরি ইনপুট ডিভাইস অনুকরণ না করে, ORION অপারেটিং সিস্টেমের ইভেন্ট কিউতে (event queue) ইনপুট ইভেন্ট ইনজেক্ট করতে পারে, যা আরও নির্ভরযোগ্য এবং দ্রুত অটোমেশন প্রদান করে।

### ৪.৯ Browser Architecture (Playwright) (বিস্তারিত)
ORION-এর `Browser Architecture` ওয়েব ব্রাউজার অটোমেশন পরিচালনা করে, যা ওয়েব-ভিত্তিক টাস্ক সম্পাদন এবং তথ্য সংগ্রহের জন্য অপরিহার্য। এটি `Playwright` ফ্রেমওয়ার্ক ব্যবহার করে, যা Chromium, Firefox এবং WebKit সমর্থন করে।
- **Browser Manager:** `BrowserManager` মডিউলটি ব্রাউজার ইনস্ট্যান্স (headless বা headful), সেশন, প্রোফাইল, কুকিজ এবং ট্যাব পরিচালনা করে। এটি একই সাথে একাধিক ব্রাউজার সেশন ম্যানেজ করতে পারে।
- **Browser Session Management:** প্রতিটি অটোমেশন টাস্কের জন্য একটি বিচ্ছিন্ন ব্রাউজার সেশন তৈরি করা হয়, যা কুকিজ, লোকাল স্টোরেজ এবং ক্যাশে আলাদা রাখে। এটি `Context Engine` (Section 4.18) এর সাথে সমন্বয় করে কাজ করে।
- **User Profiles:** ব্যবহারকারী-নির্দিষ্ট ব্রাউজার প্রোফাইল লোড করার ক্ষমতা, যা লগইন স্টেট এবং ব্যক্তিগত সেটিংস বজায় রাখে।
- **Downloads & Uploads:** স্বয়ংক্রিয়ভাবে ফাইল ডাউনলোড এবং আপলোড পরিচালনা করার ক্ষমতা। ডাউনলোড পাথ `config/system.yaml`-এ কনফিগার করা যায়।
- **Human Takeover Protocol:** ব্রাউজার অটোমেশনের সময় যদি কোনো অপ্রত্যাশিত ঘটনা ঘটে (যেমন ক্যাপচা, মাল্টি-ফ্যাক্টর অথেন্টিকেশন, বা জটিল UI ইন্টারঅ্যাকশন), `Human Takeover Protocol` (Section 4.20) ট্রিগার হয়। ORION ব্রাউজার সেশনটি পজ করে ব্যবহারকারীকে ম্যানুয়ালি নিয়ন্ত্রণ নিতে দেয় এবং কাজ শেষ হলে এজেন্ট আবার নিয়ন্ত্রণ নেয়।
- **Script Injection & Data Extraction:** ORION ওয়েবপেজে JavaScript ইনজেক্ট করে ডাইনামিকভাবে ডেটা এক্সট্র্যাক্ট করতে পারে বা নির্দিষ্ট UI উপাদানগুলোর সাথে ইন্টারঅ্যাক্ট করতে পারে।

### ৪.১০ Security Architecture (বিস্তারিত)
ORION-এর `Security Architecture` সিস্টেমের নিরাপত্তা, ডেটা সুরক্ষা এবং ব্যবহারকারীর গোপনীয়তা নিশ্চিত করে।
- **User-Controlled Permission Model:** `config/permission_config.yaml` ফাইলটি ORION-এর নিরাপত্তা নীতির কেন্দ্রবিন্দু। ব্যবহারকারী প্রতিটি টুল বা অ্যাকশনের জন্য `ALLOW`, `CONFIRM_USER`, `CONFIRM_TELEGRAM`, `ALLOW_ONCE`, `ALLOW_SESSION`, `SANDBOX_ONLY` বা `DENY` সেট করতে পারে। এটি `Zero-Policy` ধারণার একটি ব্যবহারকারী-নিয়ন্ত্রিত বাস্তবায়ন।
- **Secrets Vault:** সংবেদনশীল তথ্য যেমন API কী, পাসওয়ার্ড, এবং টোকেনগুলো `Secrets Vault` (যেমন `HashiCorp Vault` বা এনক্রিপ্টেড SQLite ডাটাবেস) এ এনক্রিপ্টেড অবস্থায় সংরক্ষণ করা হয়। রানটাইমে প্রয়োজনে এগুলো ডিক্রিপ্ট করা হয় এবং মেমরি থেকে দ্রুত মুছে ফেলা হয়।
- **Encryption:** ফাইল সিস্টেম, মেমরি এবং নেটওয়ার্ক কমিউনিকেশনে ডেটা এনক্রিপশন ব্যবহার করা হয়। `cryptography` লাইব্রেরি ব্যবহার করে ডেটা এনক্রিপ্ট ও ডিক্রিপ্ট করা হয়।
- **Audit Logs:** প্রতিটি সেনসিটিভ অ্যাকশন (যেমন ফাইল ডিলিট, sudo কমান্ড এক্সিকিউশন, লগইন) `Audit Log` এ রেকর্ড করা হয়। এই লগগুলো অপরিবর্তনীয় (immutable) এবং `Observability` (Section 4.6) ড্যাশবোর্ডে দেখা যায়।
- **Sandbox Environment:** প্লাগিন এবং অনির্ভরযোগ্য কোড `Sandbox Environment` এ এক্সিকিউট করা হয়, যা তাদের কোর সিস্টেম রিসোর্স অ্যাক্সেস সীমিত করে। `safe_mode` (config/system.yaml) ব্যবহার করে সিস্টেমকে আরও সীমাবদ্ধ করা যায়।
- **Risk Scoring:** প্রতিটি টাস্ক বা অ্যাকশনের একটি `Risk Score` থাকে, যা তার সম্ভাব্য প্রভাবের উপর ভিত্তি করে নির্ধারিত হয়। উচ্চ Risk Score-এর অ্যাকশনগুলোর জন্য অতিরিক্ত কনফার্মেশন বা অনুমোদনের প্রয়োজন হতে পারে।
- **Rollback Mechanism:** যদি কোনো অ্যাকশন সিস্টেমের ক্ষতি করে, `Self-Healing Architecture` (Section 4.5) এর `Corruption Detection` এবং `Recovery Matrix` (Section 4.21) ব্যবহার করে সিস্টেমকে পূর্ববর্তী স্থিতিশীল অবস্থায় ফিরিয়ে আনা যায়।

### ৪.১১ Learning Engine (বিস্তারিত)
ORION-এর `Learning Engine` তার অভিজ্ঞতা থেকে শেখে, যা সময়ের সাথে সাথে তার কার্যকারিতা এবং সিদ্ধান্ত গ্রহণের ক্ষমতা উন্নত করে।
- **Failure Learning:** `Recovery Matrix` (Section 4.21) এবং `Error Memory` (Section 4.1) থেকে প্রাপ্ত ডেটা ব্যবহার করে ORION শেখে কোন ধরনের ভুল কীভাবে সমাধান করা উচিত। যখন একটি টাস্ক ফেইল করে এবং সফলভাবে রিকভার হয়, তখন সেই ফেইলর প্যাটার্ন এবং রিকভারি স্ট্র্যাটেজি `Knowledge Engine` (Section 4.12) এ সেভ করা হয়।
- **Prompt Learning:** `Prompt Optimization Module` ব্যবহারকারীর দেওয়া প্রম্পট এবং LLM-এর প্রতিক্রিয়া বিশ্লেষণ করে। এটি শেখে কোন প্রম্পট ফরম্যাট, টেমপ্লেট বা নির্দেশাবলী নির্দিষ্ট টাস্কের জন্য সবচেয়ে কার্যকর। সময়ের সাথে সাথে, এটি স্বয়ংক্রিয়ভাবে প্রম্পটগুলোকে অপ্টিমাইজ করে LLM-এর পারফরম্যান্স বাড়ায়।
- **Tool Ranking & Selection:** `Tool Registry` (Section 4.4) থেকে প্রাপ্ত ডেটা এবং টুলের সফল ব্যবহারের ইতিহাস বিশ্লেষণ করে ORION শেখে কোন টাস্কের জন্য কোন টুল সবচেয়ে উপযুক্ত। এটি প্রতিটি টুলের জন্য একটি `reliability score` এবং `efficiency score` বজায় রাখে।
- **Workflow Learning:** `Workflow Engine` (Section 4.2) থেকে প্রাপ্ত সফল ওয়ার্কফ্লো প্যাটার্ন বিশ্লেষণ করে ORION ব্যবহারকারীর প্রতিদিনের কাজের প্যাটার্ন বা পুনরাবৃত্তিমূলক টাস্কগুলো শনাক্ত করে। এটি এই প্যাটার্নগুলো থেকে নতুন `Skill` (Section 4.3) বা `Workflow Template` তৈরি করার প্রস্তাব দিতে পারে।
- **Strategy Learning:** `Execution Policy` (Section 4.19) এর অধীনে, ORION শেখে কোন পরিস্থিতিতে কোন `Operating Mode` (যেমন `cpu_only` বনাম `full`) বা `Model Routing` (যেমন `local LLM` বনাম `cloud LLM`) সবচেয়ে কার্যকর। এটি তার সিদ্ধান্ত গ্রহণের প্রক্রিয়াকে ক্রমাগত ফাইন-টিউন করে।

### ৪.১২ Knowledge Engine (বিস্তারিত)
ORION-এর `Knowledge Engine` বিভিন্ন উৎস থেকে তথ্য সংগ্রহ, সংরক্ষণ, এবং পুনরুদ্ধার করে, যা এজেন্টের সিদ্ধান্ত গ্রহণ এবং টাস্ক সম্পাদনের জন্য অপরিহার্য।
- **Knowledge Graph:** `Neo4j` বা `SQLite` ভিত্তিক একটি `Knowledge Graph` ব্যবহার করে ORION বিভিন্ন সত্তা (entities), ধারণা (concepts) এবং তাদের মধ্যে সম্পর্ক (relationships) সংরক্ষণ করে। এটি এজেন্টের জন্য একটি সেম্যান্টিক নেটওয়ার্ক তৈরি করে, যা জটিল প্রশ্নাবলীর উত্তর দিতে এবং প্রাসঙ্গিক তথ্য খুঁজে পেতে সাহায্য করে।
- **Document Indexing & Embedding Pipeline:** ORION ফাইল সিস্টেমের (যেমন `docs/` ফোল্ডার) সব PDF, Word ডকুমেন্ট, Markdown ফাইল এবং অন্যান্য টেক্সট-ভিত্তিক ডেটা স্বয়ংক্রিয়ভাবে ইনডেক্স করে। এই ডকুমেন্টগুলো `Embedding Pipeline` (Python) এর মাধ্যমে ভেক্টর এম্বেডিংয়ে রূপান্তরিত হয় এবং `Vector Memory` (ChromaDB/Qdrant) এ সংরক্ষণ করা হয়।
- **Knowledge Search & Retrieval:** যখন একটি এজেন্টের তথ্যের প্রয়োজন হয়, `Knowledge Engine` `Vector Memory` এবং `Knowledge Graph` ব্যবহার করে প্রাসঙ্গিক তথ্য পুনরুদ্ধার করে। এটি `Retrieval-Augmented Generation (RAG)` প্যাটার্ন ব্যবহার করে LLM-কে আরও নির্ভুল এবং আপ-টু-ডেট তথ্য সরবরাহ করে।
- **Knowledge Update & Maintenance:** নতুন তথ্য যোগ হলে বা বিদ্যমান তথ্য পরিবর্তিত হলে `Knowledge Engine` স্বয়ংক্রিয়ভাবে তার ইনডেক্স এবং গ্রাফ আপডেট করে। এটি `Self-Healing Architecture` (Section 4.5) এর `Corruption Detection` এর সাথে সমন্বয় করে কাজ করে।
- **External Knowledge Integration:** ORION বাহ্যিক জ্ঞান উৎস (যেমন Wikipedia, Stack Overflow, বা কাস্টম ডেটাবেস) থেকে তথ্য সংগ্রহ এবং ইনডেক্স করতে পারে।

### ৪.১৩ Dependency Engine (বিস্তারিত)
ORION-এর `Dependency Engine` সিস্টেমের প্রয়োজনীয় সফটওয়্যার, লাইব্রেরি এবং বাইনারিগুলোর ইনস্টলেশন, আপডেট এবং স্বাস্থ্য পরিচালনা করে। এটি ORION-কে বিভিন্ন পরিবেশে স্বয়ংক্রিয়ভাবে কাজ করতে সাহায্য করে।
- **Dependency Detection:** বুট হওয়ার সময় এবং প্রতিটি টাস্ক এক্সিকিউশনের আগে `Dependency Engine` প্রয়োজনীয় টুলস (যেমন `nmap`, `ffmpeg`), Python প্যাকেজ (`pip`), Rust ক্রেটস (`cargo`), বা সিস্টেম লাইব্রেরি আছে কিনা তা পরীক্ষা করে। এটি `tool_config.yaml` এবং `pyproject.toml` থেকে প্রয়োজনীয় ডিপেন্ডেন্সির তালিকা পায়।
- **Auto Installer:** যদি কোনো ডিপেন্ডেন্সি মিসিং থাকে, `Dependency Engine` স্বয়ংক্রিয়ভাবে সেটিকে ইন্সটল করার চেষ্টা করে। এটি অপারেটিং সিস্টেম অনুযায়ী সঠিক প্যাকেজ ম্যানেজার (যেমন `apt`, `yum`, `brew`, `pip`, `cargo`) ব্যবহার করে। এই অ্যাকশনের জন্য `permission_config.yaml`-এ `package_install` পারমিশন প্রয়োজন।
- **Updater:** `Dependency Engine` নিয়মিত ইন্সটল করা ডিপেন্ডেন্সিগুলোর নতুন ভার্সন চেক করে এবং ব্যবহারকারীর অনুমতি নিয়ে আপডেট করার প্রস্তাব দেয়।
- **Repair:** যদি কোনো ডিপেন্ডেন্সি করাপ্টেড বা অকার্যকর হয়, `Self-Healing Architecture` (Section 4.5) এর অংশ হিসেবে `Dependency Engine` সেটিকে মেরামত বা পুনরায় ইন্সটল করার চেষ্টা করে।
- **Bootstrap:** ORION প্রথমবার রান করার সময়, `Dependency Engine` কোর ডিপেন্ডেন্সিগুলো (যেমন Python এনভায়রনমেন্ট, Rust টুলচেইন) সেটআপ করার জন্য একটি বুটস্ট্র্যাপ প্রক্রিয়া পরিচালনা করে।
- **Platform-Specific Mapping:** `tool_config.yaml`-এ `platform_mapping` ব্যবহার করে ORION বিভিন্ন অপারেটিং সিস্টেমের জন্য নির্দিষ্ট টুল বা বাইনারি পাথ ম্যাপ করতে পারে।

### ৪.১৪ Adaptive Runtime (Capability Negotiation) (বিস্তারিত)
ORION-এর `Adaptive Runtime` সিস্টেমের হার্ডওয়্যার রিসোর্স এবং অপারেটিং পরিবেশের উপর ভিত্তি করে তার আচরণ এবং কার্যকারিতা স্বয়ংক্রিয়ভাবে অপ্টিমাইজ করে। এটি ORION-কে বিভিন্ন ধরনের ডিভাইসে (লো-পাওয়ার এম্বেডেড সিস্টেম থেকে হাই-এন্ড ওয়ার্কস্টেশন) কার্যকরভাবে কাজ করতে সক্ষম করে।
- **Startup Detection & Hardware Scan:** বুট হওয়ার সময় `orion-rs/hardware_detector` (Rust) মডিউলটি CPU, GPU (যদি থাকে), RAM, Disk Space, এবং ইন্টারনেট কানেক্টিভিটি সহ সিস্টেমের সমস্ত হার্ডওয়্যার ক্যাপাবিলিটি স্ক্যান করে। এই তথ্য `system.hardware_profile` ইভেন্টের মাধ্যমে `Adaptive Runtime` এ পাঠানো হয়।
- **Capability Negotiation:** `Adaptive Runtime` প্রাপ্ত হার্ডওয়্যার প্রোফাইল এবং `config/system.yaml`-এ সংজ্ঞায়িত `operating_modes` এর উপর ভিত্তি করে সবচেয়ে উপযুক্ত `Operating Mode` (যেমন `full`, `cpu_only`, `low_memory`, `offline`, `server`, `safe`) নির্বাচন করে। এটি `system.current_operating_mode` ইভেন্ট পাবলিশ করে।
- **Dynamic Module Loading & Unloading:** `lazy_loading` পলিসি (config/system.yaml) অনুযায়ী, ORION শুধুমাত্র প্রয়োজনীয় মডিউলগুলো লোড করে। যদি `Operating Mode` পরিবর্তিত হয় (যেমন `full` থেকে `low_memory`), `Adaptive Runtime` স্বয়ংক্রিয়ভাবে ভারী মডিউলগুলো (যেমন Local LLM, Vision Engine) আনলোড করে এবং প্রয়োজনে Cloud API-তে সুইচ করে।
- **Resource Budgeting & Throttling:** `resource_budget` পলিসি (config/system.yaml) ব্যবহার করে ORION প্রতিটি মডিউল বা এজেন্টের জন্য CPU, RAM এবং অন্যান্য রিসোর্সের ব্যবহার সীমিত করে। যদি কোনো মডিউল তার বাজেট অতিক্রম করে, `Adaptive Runtime` সেটিকে `throttle` করে বা সাময়িকভাবে স্থগিত করে `RESOURCE_EXHAUSTION` (Section 4.21) ট্রিগার করে।
- **Module Priority:** `Adaptive Runtime` কোর মডিউলগুলোকে (যেমন `Event Bus`, `State Machine`) উচ্চ অগ্রাধিকার দেয়, যাতে সিস্টেমের মৌলিক কার্যকারিতা সবসময় সচল থাকে।
- **Platform-Specific Adaptation:** `platform` কনফিগারেশন (config/system.yaml) অনুযায়ী, ORION অপারেটিং সিস্টেম (Windows, Linux, macOS) এবং আর্কিটেকচার (x86_64, arm64) এর উপর ভিত্তি করে তার আচরণ এবং টুল ব্যবহার অ্যাডাপ্ট করে।

### ৪.১৫ Desktop GUI Architecture (Jarvis UX) (বিস্তারিত)
ORION-এর `Desktop GUI Architecture` ব্যবহারকারীকে একটি ইন্টারেক্টিভ এবং ভিজ্যুয়ালি সমৃদ্ধ অভিজ্ঞতা প্রদান করে, যা একটি Jarvis-সদৃশ অ্যাসিস্ট্যান্টের অনুভূতি দেয়। এটি `Tauri` ফ্রেমওয়ার্ক ব্যবহার করে, যা Rust ব্যাকএন্ড এবং React/TypeScript ফ্রন্টএন্ডকে একত্রিত করে।
- **Desktop Overlay:** ORION একটি নন-ইন্টারঅ্যাক্টিভ, ট্রান্সপারেন্ট ওভারলে উইন্ডো হিসেবে ডেস্কটপের উপরে ভাসমান (Floating Orb) থাকতে পারে। এটি সিস্টেম স্ট্যাটাস, ভয়েস অ্যানিমেশন, বা নোটিফিকেশন প্রদর্শন করে।
- **Floating Orb / Assistant Icon:** স্ক্রিনের এক কোণায় একটি ছোট, অ্যানিমেটেড আইকন থাকবে যা ORION-এর বর্তমান অবস্থা (যেমন: listening, thinking, speaking) নির্দেশ করবে। এটিতে ক্লিক করলে মূল GUI প্যানেল ওপেন হবে।
- **Notification Center:** সিস্টেমের গুরুত্বপূর্ণ ইভেন্ট, টাস্ক আপডেট, বা ব্যবহারকারীর অনুমোদনের প্রয়োজন হলে নোটিফিকেশন প্রদর্শন করবে।
- **Voice Animation & Visualizer:** ORION কথা বলার সময় একটি ভিজ্যুয়াল অ্যানিমেশন (যেমন ওয়েভফর্ম বা স্পেকট্রাম) প্রদর্শন করবে, যা ব্যবহারকারীকে অ্যাসিস্ট্যান্টের সক্রিয়তা সম্পর্কে ধারণা দেবে।
- **Live Task Panel:** একটি ডেডিকেটেড প্যানেল থাকবে যেখানে বর্তমানে চলমান টাস্ক, তাদের স্ট্যাটাস, অগ্রগতি এবং লগ লাইভ দেখা যাবে। এটি `Workflow Engine` (Section 4.2) এবং `Observability` (Section 4.6) থেকে ডেটা গ্রহণ করবে।
- **Memory Panel:** `Developer Toolkit` (Section 4.23) এর অংশ হিসেবে একটি প্যানেল থাকবে যা ORION-এর বিভিন্ন মেমরি স্তর (Session, Long-term, Semantic) এবং তাদের বিষয়বস্তু ভিজ্যুয়ালাইজ করবে।
- **System Status Panel:** CPU, RAM, Disk Usage, Network Activity, এবং `Operating Mode` (Section 4.14) সহ সিস্টেমের বর্তমান অবস্থা প্রদর্শন করবে।
- **Chat Interface:** ব্যবহারকারীর সাথে টেক্সট-ভিত্তিক ইন্টারঅ্যাকশনের জন্য একটি চ্যাট ইন্টারফেস থাকবে, যা ভয়েস কমান্ডের বিকল্প হিসেবে কাজ করবে।

### ৪.১৬ Mobile Architecture & Multi-device Sync (বিস্তারিত)
ORION-এর `Mobile Architecture` এবং `Multi-device Sync` ব্যবহারকারীকে বিভিন্ন ডিভাইস থেকে এজেন্টের সাথে ইন্টারঅ্যাক্ট করতে এবং তাদের ডেটা ও স্টেট সিঙ্ক্রোনাইজ করতে সক্ষম করে।
- **Future Flutter App:** ORION-এর একটি নেটিভ মোবাইল অ্যাপ্লিকেশন (iOS/Android) `Flutter` ব্যবহার করে তৈরি করা হবে। এই অ্যাপটি মোবাইল ডিভাইস থেকে ORION-এর কোর ফাংশনালিটি (যেমন টাস্ক ম্যানেজমেন্ট, রিমোট কন্ট্রোল, নোটিফিকেশন) অ্যাক্সেস করার জন্য একটি ইউজার ইন্টারফেস প্রদান করবে।
- **Multi-device Sync Protocol:** `orion/remote_control/sync_protocol.py` মডিউলটি ল্যাপটপ, ডেস্কটপ এবং মোবাইল ডিভাইসের মধ্যে ORION-এর `project_state`, `task_queue`, এবং `Memory` সিঙ্ক্রোনাইজ করার জন্য একটি নিরাপদ প্রোটোকল বাস্তবায়ন করবে। এটি `WebSocket` বা `MQTT` প্রোটোকল ব্যবহার করতে পারে।
- **Cloud/Local Network Sync:** সিঙ্ক্রোনাইজেশন ক্লাউড সার্ভিসের মাধ্যমে (যদি ব্যবহারকারী অনুমতি দেয়) অথবা লোকাল নেটওয়ার্কের মাধ্যমে (যেমন mDNS বা UDP ব্রডকাস্ট ব্যবহার করে ডিভাইস ডিসকভারি) হতে পারে।
- **Conflict Resolution:** যদি একাধিক ডিভাইস একই ডেটা পরিবর্তন করে, `Sync Protocol` একটি `conflict resolution` মেকানিজম ব্যবহার করে ডেটার সামঞ্জস্য নিশ্চিত করবে (যেমন `last-write-wins` বা `merge` কৌশল)।
- **Secure Pairing:** নতুন ডিভাইস যুক্ত করার জন্য একটি নিরাপদ পেয়ারিং প্রক্রিয়া (যেমন QR কোড স্ক্যান বা ওয়ান-টাইম পাসওয়ার্ড) ব্যবহার করা হবে।

### ৪.১৭ Distributed Architecture (বিস্তারিত)
ORION-এর `Distributed Architecture` ভবিষ্যতে একাধিক মেশিন বা ওয়ার্কার নোডে টাস্ক ডিস্ট্রিবিউট করার ক্ষমতা প্রদান করে, যা স্কেলেবিলিটি এবং ফল্ট টলারেন্স বাড়ায়।
- **Cluster Support:** ORION একটি `Cluster Manager` মডিউল ব্যবহার করবে যা একাধিক ORION ইনস্ট্যান্সকে একটি ক্লাস্টারে সংগঠিত করবে। প্রতিটি ইনস্ট্যান্স একটি `Worker Node` হিসেবে কাজ করবে।
- **Task Distribution:** `Workflow Engine` (Section 4.2) এবং `TaskQueueEngine` (Section 4.1) টাস্কগুলোকে ক্লাস্টারের উপলব্ধ `Worker Node`-এর মধ্যে ডিস্ট্রিবিউট করবে। `Agent Capability Advertisement` (Section 4.1) এবং `Adaptive Runtime` (Section 4.14) এর `Capability Negotiation` ব্যবহার করে টাস্কগুলো সবচেয়ে উপযুক্ত নোডে পাঠানো হবে।
- **Load Balancing:** `Cluster Manager` ওয়ার্কার নোডগুলোর মধ্যে লোড ব্যালেন্স করবে, যাতে কোনো একটি নোড ওভারলোড না হয়।
- **Fault Tolerance:** যদি একটি ওয়ার্কার নোড ফেইল করে, `Cluster Manager` সেই নোডের চলমান টাস্কগুলোকে অন্য উপলব্ধ নোডে পুনরায় অ্যাসাইন করবে। `Recovery Matrix` (Section 4.21) এই প্রক্রিয়া পরিচালনা করবে।
- **Inter-Node Communication:** ওয়ার্কার নোডগুলোর মধ্যে যোগাযোগ `Event Bus` (Section 4.1) এবং `gRPC` বা `ZeroMQ` এর মতো হাই-পারফরম্যান্স মেসেজিং প্রোটোকল ব্যবহার করে হবে।
- **Shared State:** `Multi-device Sync Protocol` (Section 4.16) এর অনুরূপ একটি মেকানিজম ব্যবহার করে ক্লাস্টারের নোডগুলোর মধ্যে `project_state` এবং `Memory` সিঙ্ক্রোনাইজ করা হবে।

### ৪.১৮ Context Engine (বিস্তারিত)
ORION-এর `Context Engine` এজেন্টের জন্য প্রাসঙ্গিক তথ্য সংগ্রহ, প্রক্রিয়াকরণ এবং উপস্থাপনা করে, যা LLM-এর কার্যকারিতা এবং সিদ্ধান্ত গ্রহণের নির্ভুলতা বাড়ায়।
- **Current Context:** `Context Engine` সবসময় এজেন্টের বর্তমান কাজের সাথে সম্পর্কিত প্রাসঙ্গিক তথ্য (যেমন বর্তমান টাস্ক, ফাইল পাথ, খোলা উইন্ডো, ব্রাউজার সেশন) ট্র্যাক করে।
- **User Context:** ব্যবহারকারীর পছন্দ, পূর্ববর্তী নির্দেশাবলী, এবং প্রোফাইল ডেটা `User Context` হিসেবে সংরক্ষণ করা হয়।
- **Workspace Context:** ORION যে ওয়ার্কস্পেসে কাজ করছে (যেমন একটি প্রজেক্ট ফোল্ডার), তার ফাইল স্ট্রাকচার, সাম্প্রতিক ফাইল পরিবর্তন, এবং Git স্ট্যাটাস `Workspace Context` হিসেবে বজায় রাখা হয়। এটি `World Model` (Section 4.18) এর `File Graph` এবং `Git Graph` থেকে ডেটা নেয়।
- **History Compression:** LLM-এর টোকেন লিমিট অতিক্রম করা এড়াতে, `Context Engine` দীর্ঘ কথোপকথন বা টাস্ক হিস্টরিকে সামারাইজ করে বা সবচেয়ে প্রাসঙ্গিক অংশগুলো নির্বাচন করে `History Compression` করে।
- **Context Ranking:** বিভিন্ন উৎস থেকে প্রাপ্ত তথ্যের প্রাসঙ্গিকতা এবং গুরুত্বের উপর ভিত্তি করে `Context Ranking` করা হয়, যাতে LLM-কে সবচেয়ে গুরুত্বপূর্ণ তথ্য প্রথমে সরবরাহ করা যায়।
- **Context Window Management:** `Model Router` (Section 4.19) এর সাথে সমন্বয় করে `Context Engine` LLM-এর `context window` এর মধ্যে ফিট করার জন্য প্রম্পট এবং ইনপুট ডেটা অপ্টিমাইজ করে। এটি `Sliding Window` বা `RAG` (Retrieval-Augmented Generation) কৌশল ব্যবহার করে।

### ৪.১৯ Execution Policy (Decision Matrix) (বিস্তারিত)
ORION-এর `Execution Policy` বা `Decision Matrix` সিস্টেমের বর্তমান অবস্থা (যেমন হার্ডওয়্যার ক্যাপাবিলিটি, অপারেটিং মোড, বাজেট) এবং টাস্কের প্রয়োজনীয়তার উপর ভিত্তি করে কোন টুল, মডেল বা কৌশল ব্যবহার করা হবে তা নির্ধারণ করে।
- **Dynamic Decision Making:** `Execution Policy Engine` রিয়েল-টাইমে `Adaptive Runtime` (Section 4.14), `Model Router` (Section 4.19), এবং `Resource Awareness` (Section 4.14) থেকে ডেটা গ্রহণ করে।
- **Policy Rules:** `config/execution_policy.yaml` (নতুন কনফিগ ফাইল) এ বিভিন্ন পলিসি রুল সংজ্ঞায়িত করা হবে। উদাহরণস্বরূপ:
  - **CPU-only Mode:** যদি `operating_mode` হয় `cpu_only`, তাহলে `Small Local Model` ব্যবহার করা হবে, `Vision` ডিজেবল থাকবে, এবং `Cloud OCR` ব্যবহার করা হবে।
  - **GPU-enabled Mode:** যদি `GPU` উপলব্ধ থাকে, তাহলে `Large Local Model` ব্যবহার করা হবে, `Parallel Vision` সক্ষম হবে, এবং `Fast Response` অগ্রাধিকার পাবে।
  - **Low Budget Mode:** যদি `Cost Manager` (Section 4.22) জানায় যে মাসিক বাজেট শেষের দিকে, তাহলে `Cloud LLM` থেকে `Local LLM`-এ সুইচ করা হবে।
- **Capability-Based Routing:** `Agent Capability Advertisement` (Section 4.1) এর উপর ভিত্তি করে টাস্কগুলো উপযুক্ত এজেন্টের কাছে পাঠানো হবে।
- **Fallback Strategies:** যদি প্রাথমিক এক্সিকিউশন পলিসি ব্যর্থ হয়, `Execution Policy` `Recovery Matrix` (Section 4.21) এর সাথে সমন্বয় করে একটি ফলব্যাক স্ট্র্যাটেজি (যেমন একটি ভিন্ন মডেল বা টুল ব্যবহার করা) নির্বাচন করবে।

### ৪.২০ Human Takeover Protocol (বিস্তারিত)
ORION-এর `Human Takeover Protocol` এমন পরিস্থিতি হ্যান্ডেল করে যখন এজেন্ট একটি টাস্ক সম্পূর্ণ করতে অক্ষম হয় (যেমন ক্যাপচা, অস্পষ্ট নির্দেশাবলী, বা জটিল নৈতিক সিদ্ধান্ত)। এই প্রোটোকল ব্যবহারকারীকে এজেন্টের নিয়ন্ত্রণ নিতে এবং সমস্যা সমাধান করতে দেয়, তারপর এজেন্ট আবার কাজ শুরু করে।
- **Trigger Conditions:** `Human Takeover` ট্রিগার হতে পারে যখন:
  - `Execution Policy` (Section 4.19) কোনো সমাধান খুঁজে পায় না।
  - `Recovery Matrix` (Section 4.21) `NOTIFY_USER` অ্যাকশন ট্রিগার করে।
  - ব্রাউজার অটোমেশনের সময় ক্যাপচা বা MFA (Multi-Factor Authentication) প্রয়োজন হয়।
  - ব্যবহারকারী ম্যানুয়ালি `takeover` কমান্ড দেয় (যেমন `/takeover` টেলিগ্রাম কমান্ড বা GUI বাটন)।
- **Pause & State Preservation:** `Human Takeover` ট্রিগার হলে, ORION তার বর্তমান টাস্ক এক্সিকিউশন `pause` করে এবং সমস্ত `runtime state` (যেমন `project_state.json`, `task_queue.json`, `browser session`) সংরক্ষণ করে।
- **User Notification:** ব্যবহারকারীকে GUI, Telegram, বা ভয়েসের মাধ্যমে জানানো হয় যে `Human Takeover` প্রয়োজন এবং কেন প্রয়োজন।
- **User Interaction:** ব্যবহারকারী GUI (Desktop Overlay), CLI, বা Telegram-এর মাধ্যমে এজেন্টের নিয়ন্ত্রণ নেয়। উদাহরণস্বরূপ, ব্রাউজার সেশনটি ব্যবহারকারীর কাছে হস্তান্তর করা হয় যাতে তিনি ম্যানুয়ালি ক্যাপচা সমাধান করতে পারেন।
- **Resume & Context Transfer:** ব্যবহারকারী সমস্যা সমাধান করার পর, ORION-কে `resume` করার নির্দেশ দেয়। ORION সংরক্ষিত স্টেট লোড করে এবং ব্যবহারকারীর করা পরিবর্তনগুলো `Context Engine` (Section 4.18) এর মাধ্যমে তার ওয়ার্কিং মেমরিতে ইনজেক্ট করে। এজেন্ট তখন কাজ আবার শুরু করে।
- **Learning from Takeover:** `Learning Engine` (Section 4.11) প্রতিটি `Human Takeover` ইভেন্ট বিশ্লেষণ করে, যাতে ভবিষ্যতে একই ধরনের পরিস্থিতিতে এজেন্ট আরও ভালোভাবে কাজ করতে পারে বা স্বয়ংক্রিয়ভাবে সমাধান খুঁজে বের করতে পারে।
### ৪.২১ Recovery Matrix (বিস্তারিত)
ORION-এর `Recovery Matrix` হলো একটি সুসংজ্ঞায়িত প্রোটোকল যা সিস্টেমের বিভিন্ন ধরনের ত্রুটি এবং ব্যর্থতা থেকে পুনরুদ্ধার করার জন্য ব্যবহৃত হয়। এটি `config/failure_matrix.yaml` ফাইল দ্বারা পরিচালিত হয়।
- **Error Classification:** `failure_matrix.yaml`-এ বিভিন্ন ধরনের ত্রুটি (যেমন `TRANSIENT`, `PERSISTENT`, `SAFETY_VIOLATION`, `LLM_HALLUCINATION`, `RESOURCE_EXHAUSTION`, `EXTERNAL_SYSTEM`, `DEPENDENCY_MISSING`) সংজ্ঞায়িত করা হয়। প্রতিটি ত্রুটির জন্য একটি `default_action` (যেমন `RETRY`, `REPLAN`, `TERMINATE`) এবং `max_retries` থাকে।
- **Recovery State Machine:** একটি ডেডিকেটেড `Recovery State Machine` (Rust বা Python) প্রতিটি ফেইলড টাস্কের জন্য রিকভারি প্রক্রিয়া পরিচালনা করে। এর স্টেটগুলো হলো `IDLE → FAILED → ANALYZING → RETRYING/REPLANNING → SUCCESS/ESCALATED`।
- **Backoff Strategies:** `TRANSIENT` ত্রুটির জন্য `exponential backoff` (যেমন 2s, 4s, 8s) ব্যবহার করা হয়, যাতে সিস্টেমকে রিকভার করার জন্য পর্যাপ্ত সময় দেওয়া যায়।
- **Contextual Analysis:** যখন একটি ত্রুটি ঘটে, `Recovery Matrix` `Context Engine` (Section 4.18) এবং `Error Memory` (Section 4.1) থেকে প্রাসঙ্গিক তথ্য সংগ্রহ করে ত্রুটির কারণ বিশ্লেষণ করে।
- **Dynamic Recovery Actions:** `Recovery Matrix` শুধুমাত্র `default_action` অনুসরণ করে না, বরং `Execution Policy` (Section 4.19) এবং `Learning Engine` (Section 4.11) থেকে প্রাপ্ত ইনসাইট ব্যবহার করে সবচেয়ে কার্যকর রিকভারি অ্যাকশন নির্বাচন করে।
- **Escalation Protocol:** যদি স্বয়ংক্রিয় রিকভারি প্রচেষ্টা ব্যর্থ হয়, `Recovery Matrix` `Human Takeover Protocol` (Section 4.20) ট্রিগার করে ব্যবহারকারীকে অবহিত করে এবং ম্যানুয়াল হস্তক্ষেপের অনুরোধ করে।
- **Rollback & Repair:** কিছু নির্দিষ্ট ত্রুটির জন্য (যেমন `Corruption Detection`), `Recovery Matrix` `Self-Healing Architecture` (Section 4.5) এর `REPAIR` প্রোটোকল ট্রিগার করে, যা সিস্টেমকে পূর্ববর্তী স্থিতিশীল অবস্থায় ফিরিয়ে আনে।

### ৪.২২ Cost Manager (বিস্তারিত)
ORION-এর `Cost Manager` LLM API কল এবং অন্যান্য ক্লাউড সার্ভিস ব্যবহারের খরচ নিরীক্ষণ, নিয়ন্ত্রণ এবং অপ্টিমাইজ করে। এটি ব্যবহারকারীকে তার বাজেট অনুযায়ী কাজ করতে সাহায্য করে।
- **Monthly Budget:** ব্যবহারকারী `config/model.yaml`-এ একটি মাসিক বাজেট (`max_monthly_budget_usd`) সেট করতে পারে। `Cost Manager` এই বাজেট মনিটর করে।
- **Real-time Cost Tracking:** `Model Router` (Section 4.19) প্রতিটি LLM API কলের টোকেন ব্যবহার এবং খরচ রিয়েল-টাইমে ট্র্যাক করে। এই ডেটা `Observability` (Section 4.6) সিস্টেমে পাঠানো হয় এবং `Cost Manager` দ্বারা একত্রিত হয়।
- **Dynamic Routing & Optimization:** যদি `Cost Manager` দেখে যে বাজেট শেষের দিকে বা অতিক্রম হয়ে গেছে, এটি `Execution Policy` (Section 4.19) কে অবহিত করে। `Execution Policy` তখন স্বয়ংক্রিয়ভাবে `Cloud LLM` থেকে `Local LLM`-এ সুইচ করে, বা কম খরচের মডেল ব্যবহার করে, অথবা কিছু ফিচার ডিজেবল করে খরচ কমাতে পারে।
- **Cost Alerts:** বাজেট ব্যবহারের একটি নির্দিষ্ট থ্রেশহোল্ড (যেমন ৮০% বা ৯০%) অতিক্রম করলে ব্যবহারকারীকে GUI, Telegram, বা ইমেলের মাধ্যমে অবহিত করা হয়।
- **Cost Breakdown:** `Developer Toolkit` (Section 4.23) এর মাধ্যমে ব্যবহারকারী LLM মডেল, API সার্ভিস, এবং অন্যান্য রিসোর্সের খরচ ব্রেকডাউন দেখতে পারে।
- **Cost Prediction:** `Cost Manager` ঐতিহাসিক ডেটা ব্যবহার করে ভবিষ্যতের খরচ অনুমান করতে পারে এবং ব্যবহারকারীকে সম্ভাব্য বাজেট অতিক্রম সম্পর্কে সতর্ক করতে পারে।

### ৪.২৩ Developer Toolkit (বিস্তারিত)
ORION-এর `Developer Toolkit` ডেভেলপার এবং অ্যাডভান্সড ব্যবহারকারীদের জন্য সিস্টেমের অভ্যন্তরীণ অবস্থা নিরীক্ষণ, ডিবাগিং এবং কাস্টমাইজ করার জন্য শক্তিশালী টুলস সরবরাহ করে।
- **Debug Console:** একটি রিয়েল-টাইম কনসোল যা সিস্টেমের লগ, ইভেন্ট এবং এজেন্টদের অভ্যন্তরীণ স্টেট প্রদর্শন করে। এটি `Observability` (Section 4.6) থেকে ডেটা গ্রহণ করে।
- **Task Viewer:** `Workflow Engine` (Section 4.2) দ্বারা পরিচালিত `Task Graph` এবং `Task Queue` (Section 4.1) এর লাইভ ভিজ্যুয়ালাইজেশন। এটি প্রতিটি টাস্কের স্ট্যাটাস, ডিপেন্ডেন্সি এবং অগ্রগতি দেখায়।
- **Memory Viewer:** ORION-এর 4-Tier Memory Architecture (Session, Long-term, Episodic, Semantic) এর বিষয়বস্তু এবং তাদের ইন্টারকানেকশন ভিজ্যুয়ালাইজ করার জন্য একটি ইন্টারঅ্যাক্টিভ টুল।
- **Workflow Editor:** ব্যবহারকারী বা ডেভেলপারদের জন্য বিদ্যমান `Skill` (Section 4.3) বা `Workflow` (Section 4.2) পরিবর্তন করতে বা নতুন তৈরি করতে একটি গ্রাফিক্যাল ইন্টারফেস।
- **Prompt Editor:** LLM প্রম্পট টেমপ্লেট তৈরি, পরীক্ষা এবং অপ্টিমাইজ করার জন্য একটি টুল। এটি `Learning Engine` (Section 4.11) এর `Prompt Learning` মডিউলের সাথে সমন্বয় করে।
- **Event Viewer:** `Event Bus` (Section 4.1) এর মাধ্যমে প্রবাহিত সমস্ত ইভেন্টের একটি টাইমলাইন ভিউ। এটি ইভেন্ট ফিল্টারিং এবং সার্চিং সমর্থন করে।
- **Plugin Manager:** ইনস্টল করা প্লাগিনগুলো দেখতে, নতুন প্লাগিন ইন্সটল করতে, আপডেট করতে বা ডিজেবল করতে একটি GUI টুল।
- **Configuration Editor:** `config/` ফোল্ডারের সমস্ত YAML ফাইল (system, model, permission, tool, voice, telegram, failure_matrix) এডিট করার জন্য একটি ইউজার-ফ্রেন্ডলি ইন্টারফেস।

### ৪.২৪ Testing Architecture (বিস্তারিত)
ORION-এর `Testing Architecture` সিস্টেমের নির্ভরযোগ্যতা, কার্যকারিতা এবং স্থিতিশীলতা নিশ্চিত করার জন্য একটি ব্যাপক টেস্টিং ফ্রেমওয়ার্ক প্রদান করে।
- **Unit Tests:** প্রতিটি মডিউল, ক্লাস এবং ফাংশনের জন্য `pytest` ব্যবহার করে ইউনিট টেস্ট লেখা হবে। এটি কোডের ক্ষুদ্রতম অংশগুলোর সঠিক কার্যকারিতা যাচাই করে।
- **Integration Tests:** বিভিন্ন মডিউল বা এজেন্টের মধ্যে ইন্টারঅ্যাকশন এবং ডেটা ফ্লো সঠিকভাবে কাজ করছে কিনা তা যাচাই করার জন্য ইন্টিগ্রেশন টেস্ট লেখা হবে। উদাহরণস্বরূপ, `Event Bus` এবং `Agent Registry` এর মধ্যে যোগাযোগ।
- **End-to-End (E2E) Tests:** `Playwright` এবং `Tauri` টেস্টিং ইউটিলিটি ব্যবহার করে সম্পূর্ণ ওয়ার্কফ্লো (যেমন একটি Skill এক্সিকিউশন, একটি ব্রাউজার অটোমেশন টাস্ক) শুরু থেকে শেষ পর্যন্ত পরীক্ষা করা হবে।
- **Performance Tests:** `locust` বা `pytest-benchmark` ব্যবহার করে সিস্টেমের পারফরম্যান্স (যেমন টাস্ক ল্যাটেন্সি, থ্রুপুট) বিভিন্ন লোড কন্ডিশনে পরীক্ষা করা হবে।
- **Stress Tests:** সিস্টেমের ব্রেকিং পয়েন্ট খুঁজে বের করার জন্য এবং উচ্চ লোডে তার আচরণ যাচাই করার জন্য স্ট্রেস টেস্ট করা হবে।
- **Security Tests:** `OWASP ZAP` বা `bandit` এর মতো টুল ব্যবহার করে নিরাপত্তা দুর্বলতা (যেমন ইনজেকশন অ্যাটাক, ডেটা লিক) পরীক্ষা করা হবে।
- **Regression Tests:** নতুন ফিচার যোগ বা বাগ ফিক্স করার পর যেন বিদ্যমান কার্যকারিতা নষ্ট না হয়, তার জন্য রিগ্রেশন টেস্ট স্যুট তৈরি করা হবে।
- **Test Gates & CI/CD:** প্রতিটি কোড কমিটের আগে স্বয়ংক্রিয়ভাবে টেস্ট রান করা হবে এবং টেস্ট পাস না হলে মার্জ ব্লক করা হবে। এটি `GitHub Actions` বা `GitLab CI` এর মাধ্যমে বাস্তবায়িত হবে।

### ৪.২৫ Context Window Management (বিস্তারিত)
ORION-এর `Context Window Management` LLM-এর টোকেন লিমিট কার্যকরভাবে পরিচালনা করে, যাতে দীর্ঘ কথোপকথন, বড় ডকুমেন্ট বা জটিল টাস্কের সময়ও LLM প্রাসঙ্গিক তথ্য অ্যাক্সেস করতে পারে এবং `OutOfContext` এরর এড়ানো যায়।
- **Token Estimation:** প্রতিটি LLM কলের আগে, `Context Engine` (Section 4.18) ইনপুট প্রম্পট, চ্যাট হিস্টরি, এবং অন্যান্য প্রাসঙ্গিক ডেটার টোকেন সংখ্যা অনুমান করে।
- **Sliding Window:** দীর্ঘ কথোপকথনের জন্য, `Context Engine` একটি `sliding window` কৌশল ব্যবহার করে। এটি শুধুমাত্র সাম্প্রতিকতম এবং সবচেয়ে প্রাসঙ্গিক কথোপকথনের অংশগুলোকে LLM-এর `context window`-এর মধ্যে রাখে, পুরানো বা কম প্রাসঙ্গিক অংশগুলোকে ট্রাঙ্কেট করে।
- **Retrieval-Augmented Generation (RAG):** যখন LLM-এর কাছে এমন তথ্যের প্রয়োজন হয় যা তার `context window`-এর বাইরে, `Knowledge Engine` (Section 4.12) `Vector Memory` থেকে প্রাসঙ্গিক ডকুমেন্ট বা তথ্য পুনরুদ্ধার করে এবং সেগুলোকে প্রম্পটের সাথে ইনজেক্ট করে। এটি LLM-কে আপ-টু-ডেট এবং ডোমেইন-নির্দিষ্ট তথ্য অ্যাক্সেস করতে সক্ষম করে।
- **Context Compression:** `History Compression` (Section 4.18) এর মাধ্যমে দীর্ঘ টেক্সট বা কথোপকথনগুলোকে সামারাইজ করে টোকেন সংখ্যা কমানো হয়।
- **Dynamic Context Adjustment:** `Adaptive Runtime` (Section 4.14) এবং `Model Router` (Section 4.19) এর সাথে সমন্বয় করে `Context Window Management` বর্তমান `Operating Mode` এবং ব্যবহৃত LLM মডেলের `context window` এর উপর ভিত্তি করে তার আচরণ অ্যাডাপ্ট করে। উদাহরণস্বরূপ, একটি ছোট `context window` সহ মডেলের জন্য আরও কঠোর কম্প্রেশন প্রয়োগ করা হয়।
- **User Preference:** ব্যবহারকারী `config/context.yaml` (নতুন কনফিগ ফাইল) এ `context window` এর আকার, কম্প্রেশন কৌশল, এবং RAG এর অগ্রাধিকার সেট করতে পারে।
