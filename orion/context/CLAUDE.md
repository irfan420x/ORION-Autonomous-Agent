# CLAUDE.md - Context Subsystem

## 1. Overview
ORION's Context Subsystem is responsible for gathering, processing, and presenting relevant information to the LLM, enhancing its effectiveness and decision-making accuracy. It manages various types of context, including current task, user preferences, and workspace state, while optimizing for LLM token limits.

## 2. Components
- **ContextEngine (`context_engine.py`):** The central component that aggregates and manages different context types (Current, User, Workspace).
- **HistoryCompressor (`history_compressor.py`):** Reduces the token count of long conversations or task histories through summarization or selection of most relevant parts.
- **ContextWindowOptimizer (`context_window_optimizer.py`):** Adjusts context to fit within LLM token limits, employing strategies like sliding windows and RAG.

## 3. Interfaces (Contracts)
Context-related data structures and interfaces are defined in `orion/contracts/context_contracts.py`.

### 3.1 ContextEngine Interface
- `async get_current_context(task_id: TaskID) -> ContextBundle`: Retrieves a comprehensive context bundle for a given task.
- `async update_user_context(user_id: str, preferences: Dict[str, Any])`: Updates user-specific contextual information.
- `async get_workspace_context(path: str) -> WorkspaceContext`: Retrieves context related to a specific workspace path.

### 3.2 HistoryCompressor Interface
- `async compress_history(history: List[str], target_tokens: int) -> List[str]`: Compresses a list of historical messages to fit within a target token count.

### 3.3 ContextWindowOptimizer Interface
- `async optimize_context(prompt: str, current_context: ContextBundle, llm_model: str) -> OptimizedContext`: Optimizes the context to fit the LLM's window, potentially using RAG.

## 4. Dependencies
- **Internal:** `orion.contracts.context_contracts`, `orion.core.communication.event_bus`, `orion.memory.semantic_memory`, `orion.knowledge.knowledge_engine`
- **External:** `tiktoken` (for token estimation), `asyncio`

## 5. Build Order & Verification (Phase 1 - M1.4)
1. Define context-related Pydantic models in `orion/contracts/context_contracts.py`.
2. Implement `HistoryCompressor` with basic summarization/truncation logic.
3. Implement `ContextWindowOptimizer` with token estimation and simple sliding window.
4. Implement `ContextEngine` to integrate various context sources.
5. Create a demo script (`examples/context_engine_demo.py`) to demonstrate context aggregation and optimization.
6. Ensure unit tests for all context modules pass.
