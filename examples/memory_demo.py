"""
Memory Subsystem Demo
=====================
Demonstrates ORION's 4-Tier Memory Architecture.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from orion.memory.session_memory import SessionMemory
from orion.memory.long_term_memory import LongTermMemory
from orion.memory.semantic_memory import SemanticMemory
from orion.core.communication.event_bus import EventBus

async def main():
    print("--- Memory Subsystem Demo Start ---")

    # EventBus is required by all memory modules
    event_bus = EventBus()

    # 1. Session Memory (in-memory, fast)
    session_mem = SessionMemory(event_bus)
    await session_mem.put("user_name", "Alice")
    await session_mem.put("current_task", "Analyze sales report")
    print(f"Session Memory: user_name = {await session_mem.get('user_name')}")
    print(f"Session Memory: current_task = {await session_mem.get('current_task')}")

    # 2. Long-Term Memory (SQLite-backed)
    db_path = "state/demo_memory.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    long_term_mem = LongTermMemory(event_bus, db_path)
    await long_term_mem.start()
    await long_term_mem.put("favorite_color", "blue", tags=["user_pref"])
    await long_term_mem.put("project_deadline", "2026-12-31", tags=["project"])
    print(f"Long-Term Memory: favorite_color = {await long_term_mem.get('favorite_color')}")
    print(f"Long-Term Memory: project_deadline = {await long_term_mem.get('project_deadline')}")

    # Search in long-term memory
    results = await long_term_mem.search("color")
    print(f"Long-Term search 'color': {len(results)} results")

    # 3. Semantic Memory (vector search with mock embeddings)
    semantic_mem = SemanticMemory(event_bus)
    await semantic_mem.add_document("doc1", "ORION is an autonomous OS agent.", metadata={"type": "architecture"})
    await semantic_mem.add_document("doc2", "The Event Bus uses asyncio queues.", metadata={"type": "communication"})
    await semantic_mem.add_document("doc3", "Python is used for AI engine.", metadata={"type": "tech_stack"})

    print("\nSemantic Memory Search for 'OS agent':")
    results = await semantic_mem.search("OS agent", top_k=2)
    for res in results:
        print(f"  Doc: {res['doc_id']}, Score: {res.get('score', 'N/A'):.3f}")

    # Stats
    print("\n--- Session Memory Stats ---")
    for k, v in session_mem.get_stats().model_dump().items():
        print(f"  {k}: {v}")

    print("\n--- Long-Term Memory Stats ---")
    for k, v in long_term_mem.get_stats().model_dump().items():
        print(f"  {k}: {v}")

    print("\n--- Semantic Memory Stats ---")
    for k, v in semantic_mem.get_stats().items():
        print(f"  {k}: {v}")

    # Cleanup demo DB
    await long_term_mem.stop()
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(db_path + "-wal"):
        os.remove(db_path + "-wal")
    if os.path.exists(db_path + "-shm"):
        os.remove(db_path + "-shm")

    print("\n--- Memory Subsystem Demo End ---")

if __name__ == "__main__":
    asyncio.run(main())
