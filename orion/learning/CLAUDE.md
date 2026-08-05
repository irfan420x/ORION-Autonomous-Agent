"""# CLAUDE.md - Learning Subsystem

## 1. Overview
ORION's Learning Subsystem enables the agent to continuously improve its performance, decision-making, and problem-solving capabilities by learning from its experiences. It analyzes past successes and failures, optimizes strategies, and refines its understanding of the environment and user preferences.

## 2. Components
- **LearningEngine (`learning_engine.py`):** Orchestrates various learning processes, integrating insights from different learning modules.
- **FailureLearner (`failure_learner.py`):** Analyzes task failures and successful recovery attempts to identify patterns and improve future recovery strategies.
- **PromptOptimizer (`prompt_optimizer.py`):** Learns from LLM interactions to refine prompt templates and instructions, maximizing LLM effectiveness and reducing token usage.
- **ToolLearner (`tool_learner.py`):** Evaluates tool usage, success rates, and efficiency to improve tool selection and application for specific tasks.
- **WorkflowLearner (`workflow_learner.py`):** Identifies recurring task patterns and successful workflows, suggesting new skills or optimizing existing ones.

## 3. Interfaces (Contracts)
Learning-related data structures are defined in `orion/contracts/learning_contracts.py`.

### 3.1 LearningEngine Interface
- `async process_feedback(feedback: LearningFeedback)`: Processes feedback from various sources to trigger learning processes.
- `async get_optimized_strategy(task: Task) -> LearningStrategy`: Retrieves an optimized strategy based on past learning.

### 3.2 FailureLearner Interface
- `async analyze_failure(failure_report: FailureReport)`: Analyzes a specific failure event and updates failure patterns.

### 3.3 PromptOptimizer Interface
- `async optimize_prompt(original_prompt: str, llm_response: LLMResponse, task_outcome: TaskOutcome) -> str`: Refines a prompt based on LLM response and task outcome.

## 4. Dependencies
- **Internal:** `orion.contracts.learning_contracts`, `orion.contracts.agent_contracts`, `orion.contracts.router_contracts`, `orion.core.communication.event_bus`, `orion.knowledge.knowledge_engine`, `orion.intelligence.reasoning.reflection_engine`
- **External:** `asyncio`, `scikit-learn` (for basic pattern recognition, if needed).

## 5. Build Order & Verification (Phase 7 - M7.2)
1. Define learning-related Pydantic models in `orion/contracts/learning_contracts.py`.
2. Implement `FailureLearner` to store and retrieve simple failure patterns.
3. Implement `PromptOptimizer` with basic prompt modification based on success/failure.
4. Implement `ToolLearner` to track tool usage statistics.
5. Implement `LearningEngine` to integrate these modules.
6. Create a demo script (`examples/learning_engine_demo.py`) to demonstrate a simple learning cycle.
7. Ensure unit tests for all Learning modules pass.
"""
