import asyncio
import time
from orion.context.context_engine import ContextEngine
from orion.context.history_compressor import HistoryCompressor
from orion.context.context_window_optimizer import ContextWindowOptimizer
from orion.contracts.context_contracts import UserContext, WorkspaceContext, ContextBundle, OptimizedContext
from orion.contracts.agent_contracts import TaskID

async def main():
    print("--- Context Engine Demo Start ---")

    # Mock dependencies
    class MockSemanticMemory:
        async def search(self, query: str, top_k: int) -> list:
            print(f"[MockSemanticMemory] Searching for: {query}")
            return [{"doc_id": "doc_mock", "content": "Mock document content.", "score": 0.9}]

    class MockKnowledgeEngine:
        def __init__(self):
            self.semantic_memory = MockSemanticMemory()

    # Initialize components
    history_compressor = HistoryCompressor()
    context_window_optimizer = ContextWindowOptimizer(MockKnowledgeEngine())
    context_engine = ContextEngine(history_compressor, context_window_optimizer)

    # Create mock contexts
    user_ctx = UserContext(user_id="test_user", preferences={"theme": "dark"})
    workspace_ctx = WorkspaceContext(path="/home/user/project", recent_files=["main.py", "config.yaml"])
    chat_history = [
        {"role": "user", "content": "Hello, ORION."},
        {"role": "assistant", "content": "How can I help you?"},
        {"role": "user", "content": "I need to analyze some data from the sales report."}
    ]

    # Get a context bundle
    bundle = await context_engine.get_current_context(
        task_id=TaskID("task_001"),
        user_context=user_ctx,
        workspace_context=workspace_ctx,
        chat_history=chat_history
    )
    print("\n--- Context Bundle ---")
    print(bundle.model_dump_json(indent=2))

    # Simulate compression
    long_text = "This is a very long piece of text that needs to be compressed to fit into a smaller context window. It contains many words and sentences that might exceed the token limit of an LLM. The compressor should be able to summarize or truncate this effectively." * 10
    compressed_history = await history_compressor.compress_history([long_text], target_tokens=50)
    print("\n--- Compressed History ---")
    print(compressed_history[0][:100] + "...") # Print first 100 chars

    # Simulate optimization for LLM
    optimized_prompt = await context_window_optimizer.optimize_context(
        prompt="Summarize the sales report.",
        current_context=bundle,
        llm_model="mock_llm"
    )
    print("\n--- Optimized Prompt for LLM ---")
    print(optimized_prompt.model_dump_json(indent=2))

    print("--- Context Engine Demo End ---")

if __name__ == "__main__":
    # This will fail until context modules are implemented
    try:
        asyncio.run(main())
    except NotImplementedError as e:
        print(f"\nERROR: {e}. Please implement context module methods first.")

