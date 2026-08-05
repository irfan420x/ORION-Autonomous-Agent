# CLAUDE.md - Memory Subsystem

## 1. Overview
ORION's Memory Subsystem is a crucial component that provides a multi-tiered approach to information storage and retrieval. It's designed to handle various types of data, from short-term session context to long-term knowledge, ensuring that the agent has access to relevant information at all times.

## 2. Components
- **Session Memory (`session_memory.py`):** Stores ephemeral, short-term context relevant to the current interaction or task. Typically in-memory.
- **Working Memory (`working_memory.py`):** Holds active data, intermediate results, and current task-specific information. More persistent than session memory but still task-bound.
- **Long-Term Memory (`long_term_memory.py`):** Stores persistent knowledge, past experiences, user preferences, and learned patterns. Often backed by a local database (e.g., SQLite).
- **Semantic Memory (`semantic_memory.py`):** Stores vector embeddings of documents, code, and other unstructured data, enabling semantic search and Retrieval-Augmented Generation (RAG). Backed by a vector database (e.g., ChromaDB, Qdrant).

## 3. Interfaces (Contracts)
Memory-related data structures and interfaces are defined in `orion/contracts/memory_contracts.py`.

### 3.1 Memory Interfaces (Common)
- `async store(key: str, value: Any)`: Stores a value associated with a key.
- `async retrieve(key: str) -> Any`: Retrieves a value by its key.
- `async delete(key: str)`: Deletes a stored item.
- `async clear()`: Clears all items from the memory.

### 3.2 Semantic Memory Specific Interface
- `async add_document(doc_id: str, content: str, metadata: Dict[str, Any])`: Adds a document to the vector store.
- `async search(query: str, top_k: int) -> List[Dict[str, Any]]`: Performs a semantic search and returns top_k relevant documents.

## 4. Dependencies
- **Internal:** `orion.contracts.memory_contracts`, `orion.core.communication.event_bus`
- **External:** `SQLite` (for Long-Term Memory), `ChromaDB`/`Qdrant` (for Semantic Memory), `asyncio`.

## 5. Build Order & Verification (Phase 1 - M1.3)
1. Define memory-related Pydantic models in `orion/contracts/memory_contracts.py`.
2. Implement `SessionMemory` (simple in-memory dictionary).
3. Implement `LongTermMemory` (SQLite wrapper).
4. Implement `SemanticMemory` (initially with a mock or in-memory vector store, later integrate ChromaDB/Qdrant).
5. Create a demo script (`examples/memory_demo.py`) to demonstrate storing and retrieving data from all memory tiers.
6. Ensure unit tests for all memory modules pass.
