import asyncio
import time
import os
from orion.memory.session_memory import SessionMemory
from orion.memory.long_term_memory import LongTermMemory
from orion.memory.semantic_memory import SemanticMemory
from orion.contracts.memory_contracts import MemoryItem, Document, SearchResult

async def main():
    print("--- Memory Subsystem Demo Start ---")

    # 1. Session Memory
    session_mem = SessionMemory()
    await session_mem.store("user_name", "Alice")
    await session_mem.store("current_task", "Analyze sales report")
    print(f"Session Memory: user_name = {await session_mem.retrieve("user_name")}")
    print(f"Session Memory: current_task = {await session_mem.retrieve("current_task")}")

    # 2. Long-Term Memory (SQLite)
    db_path = "state/long_term_memory.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    long_term_mem = LongTermMemory(db_path)
    await long_term_mem.store("favorite_color", "blue", metadata={"source": "user_pref"})
    await long_term_mem.store("project_deadline", "2026-12-31", metadata={"source": "project_plan"})
    print(f"Long-Term Memory: favorite_color = {await long_term_mem.retrieve("favorite_color")}")
    print(f"Long-Term Memory: project_deadline = {await long_term_mem.retrieve("project_deadline")}")

    # 3. Semantic Memory (Mock for now)
    semantic_mem = SemanticMemory()
    doc1 = Document(doc_id="doc1", content="ORION is an autonomous OS agent.", metadata={"type": "architecture"})
    doc2 = Document(doc_id="doc2", content="The Event Bus uses asyncio queues.", metadata={"type": "communication"})
    doc3 = Document(doc_id="doc3", content="Python is used for AI engine.", metadata={"type": "tech_stack"})

    await semantic_mem.add_document(doc1.doc_id, doc1.content, doc1.metadata)
    await semantic_mem.add_document(doc2.doc_id, doc2.content, doc2.metadata)
    await semantic_mem.add_document(doc3.doc_id, doc3.content, doc3.metadata)

    print("\nSemantic Memory Search for 'OS agent':")
    results = await semantic_mem.search("OS agent", top_k=1)
    for res in results:
        print(f"  Doc ID: {res.doc_id}, Content: {res.content}, Score: {res.score}")

    print("--- Memory Subsystem Demo End ---")

if __name__ == "__main__":
    # This will fail until memory modules are implemented
    try:
        asyncio.run(main())
    except NotImplementedError as e:
        print(f"\nERROR: {e}. Please implement memory module methods first.")

