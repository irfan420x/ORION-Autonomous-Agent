"""# CLAUDE.md - Execution Policy Subsystem

## 1. Overview
ORION's Execution Policy Subsystem, also known as the Decision Matrix, is responsible for dynamically determining the optimal tools, models, and strategies to use for a given task. It makes decisions based on the current system state, available resources, operating mode, and task requirements, ensuring efficient and cost-effective execution.

## 2. Components
- **ExecutionPolicyEngine (`policy_engine.py`):** Evaluates various factors (hardware, operating mode, budget, task type) and selects the most appropriate execution strategy.
- **PolicyEvaluator (`policy_evaluator.py`):** Contains the logic for evaluating policy rules defined in `config/execution_policy.yaml`.

## 3. Interfaces (Contracts)
Execution policy-related data structures are defined in `orion/contracts/policy_contracts.py`.

### 3.1 ExecutionPolicyEngine Interface
- `async determine_strategy(task: Task, current_context: ContextBundle) -> ExecutionStrategy`: Determines the best strategy for a given task and context.
- `async evaluate_policy(policy_name: str, criteria: Dict[str, Any]) -> bool`: Evaluates a specific policy rule against given criteria.

## 4. Dependencies
- **Internal:** `orion.contracts.policy_contracts`, `orion.contracts.agent_contracts`, `orion.contracts.context_contracts`, `orion.core.communication.event_bus`, `orion.core.runtime.adaptive_runtime`, `orion.resource.resource_manager`, `orion.intelligence.router.model_router`
- **External:** `asyncio`, `pyyaml` (for config parsing).

## 5. Build Order & Verification (Phase 3 - M3.2)
1. Define policy-related Pydantic models in `orion/contracts/policy_contracts.py`.
2. Create `config/execution_policy.yaml` with initial policy rules (e.g., `cpu_only` mode uses local LLM).
3. Implement `PolicyEvaluator` to read and evaluate rules from the config file.
4. Implement `ExecutionPolicyEngine` to integrate inputs from `AdaptiveRuntime`, `ResourceManager`, and `ModelRouter`.
5. Create a demo script (`examples/policy_engine_demo.py`) to demonstrate dynamic strategy determination.
6. Ensure unit tests for `ExecutionPolicyEngine` pass.
"""
