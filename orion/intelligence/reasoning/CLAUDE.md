"""# CLAUDE.md - Reasoning Subsystem

## 1. Overview
ORION's Reasoning Subsystem is responsible for the agent's cognitive processes, enabling it to perform logical inference, problem-solving, and decision-making. It works in conjunction with the Planning Engine to refine plans and with the Verification Engine to validate outcomes.

## 2. Components
- **ReasoningEngine (`reasoning_engine.py`):** The core component that applies logical rules and heuristics to derive conclusions from available context and knowledge.
- **ReflectionEngine (`reflection_engine.py`):** Enables the agent to introspect on its past actions, identify errors, and learn from experience.
- **VerificationEngine (`verification_engine.py`):** Validates the correctness of plans, execution steps, and outcomes against predefined criteria or expected results.

## 3. Interfaces (Contracts)
Reasoning-related data structures are defined in `orion/contracts/reasoning_contracts.py`.

### 3.1 ReasoningEngine Interface
- `async infer(context: ContextBundle, query: str) -> InferenceResult`: Performs logical inference based on the given context and query.
- `async solve_problem(problem: ProblemStatement) -> Solution`: Attempts to solve a defined problem.

### 3.2 ReflectionEngine Interface
- `async reflect_on_task(task: Task, outcome: TaskOutcome) -> ReflectionReport`: Analyzes a completed task and its outcome to identify lessons learned.

### 3.3 VerificationEngine Interface
- `async verify_plan(plan: TaskGraph) -> VerificationResult`: Checks the logical consistency and feasibility of a task plan.
- `async verify_outcome(task: Task, actual_outcome: Any, expected_outcome: Any) -> VerificationResult`: Compares actual task outcomes against expected results.

## 4. Dependencies
- **Internal:** `orion.contracts.reasoning_contracts`, `orion.contracts.context_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.knowledge.knowledge_engine`, `orion.intelligence.clients.llm_client`
- **External:** `asyncio`.

## 5. Build Order & Verification (Phase 3 - M3.4)
1. Define reasoning-related Pydantic models in `orion/contracts/reasoning_contracts.py`.
2. Implement `ReasoningEngine` with basic inference capabilities.
3. Implement `ReflectionEngine` to analyze simple task outcomes.
4. Implement `VerificationEngine` to check basic plan validity.
5. Create a demo script (`examples/reasoning_demo.py`) to demonstrate inference, reflection, and verification.
6. Ensure unit tests for all reasoning modules pass.
"""
