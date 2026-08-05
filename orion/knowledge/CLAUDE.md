"""# CLAUDE.md - Knowledge Subsystem

## 1. Overview
ORION's Knowledge Subsystem is responsible for acquiring, storing, organizing, and retrieving information from various sources. It acts as the agent's long-term memory and reference library, providing factual data, learned patterns, and contextual understanding to support reasoning and decision-making.

## 2. Components
- **KnowledgeEngine (`knowledge_engine.py`):** The central component that orchestrates knowledge acquisition, indexing, search, and retrieval across different knowledge sources.
- **KnowledgeGraph (`knowledge_graph.py`):** Stores structured knowledge in a graph format (entities, relationships), enabling complex queries and inferencing.
- **DocumentIndexer (`document_indexer.py`):** Processes and indexes various document types (text, PDF, Markdown) for efficient search and retrieval.
- **EmbeddingPipeline (`embedding_pipeline.py`):** Converts textual content into vector embeddings for semantic search capabilities within the Semantic Memory.

## 3. Interfaces (Contracts)
Knowledge-related data structures are defined in `orion/contracts/knowledge_contracts.py`.

### 3.1 KnowledgeEngine Interface
- `async add_knowledge(item: KnowledgeItem)`: Adds a new piece of knowledge to the system.
- `async retrieve_knowledge(query: str, top_k: int) -> List[KnowledgeItem]`: Retrieves relevant knowledge based on a query.
- `async update_knowledge(item: KnowledgeItem)`: Updates an existing knowledge item.

### 3.2 KnowledgeGraph Interface
- `async add_entity(entity: GraphEntity)`: Adds a new entity to the knowledge graph.
- `async add_relationship(relationship: GraphRelationship)`: Adds a new relationship between entities.
- `async query_graph(query: str) -> List[GraphQueryResult]`: Queries the knowledge graph using a graph query language.

### 3.3 DocumentIndexer Interface
- `async index_document(document: Document)`: Indexes a document for full-text and semantic search.
- `async search_documents(query: str, top_k: int) -> List[SearchResult]`: Searches indexed documents.

## 4. Dependencies
- **Internal:** `orion.contracts.knowledge_contracts`, `orion.contracts.memory_contracts`, `orion.core.communication.event_bus`, `orion.memory.semantic_memory`, `orion.intelligence.clients.llm_client`
- **External:** `Neo4j` (for Knowledge Graph, optional), `SQLite` (for simpler graph storage), `asyncio`, `pypdf` (for PDF parsing), `langchain` (for document loaders/splitters).

## 5. Build Order & Verification (Phase 7 - M7.3)
1. Define knowledge-related Pydantic models in `orion/contracts/knowledge_contracts.py`.
2. Implement `EmbeddingPipeline` to generate embeddings for text (using a mocked LLM client initially).
3. Implement `DocumentIndexer` to process and index text files.
4. Implement `KnowledgeGraph` (initially with SQLite, later with Neo4j if needed).
5. Implement `KnowledgeEngine` to integrate document indexing and graph querying.
6. Create a demo script (`examples/knowledge_engine_demo.py`) to demonstrate adding documents, querying the graph, and semantic search.
7. Ensure unit tests for all Knowledge modules pass.
"""
