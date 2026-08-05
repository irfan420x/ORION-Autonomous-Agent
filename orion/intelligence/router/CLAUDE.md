"""# CLAUDE.md - Model Router Subsystem

## 1. Overview
ORION's Model Router Subsystem is responsible for intelligently selecting and routing requests to the most appropriate Large Language Model (LLM) or other AI models. This decision is based on factors such as task requirements, cost, latency, available resources (local vs. cloud), and model capabilities, ensuring optimal performance and cost efficiency.

## 2. Components
- **ModelRouter (`model_router.py`):** The core component that evaluates routing policies and selects the best model for a given request.
- **CostManager (`cost_manager.py`):** Tracks LLM token usage and associated costs, enforcing budget constraints.
- **ModelRegistry (`model_registry.py`):** Maintains a list of available local and cloud models, their capabilities, and pricing.

## 3. Interfaces (Contracts)
Model routing and cost-related data structures are defined in `orion/contracts/router_contracts.py`.

### 3.1 ModelRouter Interface
- `async route_llm_request(request: LLMRequest) -> LLMResponse`: Routes an LLM request to the selected model and returns its response.
- `async select_model(task_type: str, context: ContextBundle) -> ModelInfo`: Selects the optimal model based on task and context.

### 3.2 CostManager Interface
- `async record_usage(model_id: str, tokens_used: int, cost: float)`: Records LLM usage and cost.
- `async get_current_cost() -> CostReport`: Retrieves current cost usage and budget status.

## 4. Dependencies
- **Internal:** `orion.contracts.router_contracts`, `orion.contracts.context_contracts`, `orion.core.communication.event_bus`, `orion.intelligence.clients.llm_client`, `orion.config.model_config`
- **External:** `asyncio`, `pyyaml` (for config parsing).

## 5. Build Order & Verification (Phase 3 - M3.2)
1. Define model routing and cost-related Pydantic models in `orion/contracts/router_contracts.py`.
2. Implement `ModelRegistry` to load model configurations from `config/model.yaml`.
3. Implement `CostManager` to track usage and enforce budget (initially with mock data).
4. Implement `ModelRouter` to select models based on simple rules (e.g., prefer local if available).
5. Create a demo script (`examples/model_router_demo.py`) to demonstrate model selection and cost tracking.
6. Ensure unit tests for `ModelRouter` and `CostManager` pass.
"""
