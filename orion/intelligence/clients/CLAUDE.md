"""# CLAUDE.md - LLM Clients Subsystem

## 1. Overview
ORION's LLM Clients Subsystem provides standardized interfaces for interacting with various Large Language Models (LLMs), both local and cloud-based. It abstracts away the complexities of different LLM APIs, allowing the Model Router and other intelligence components to interact with LLMs uniformly.

## 2. Components
- **LLMClient (`llm_client.py`):** A generic interface for all LLM interactions.
- **OpenAIClient (`openai_client.py`):** Specific client for OpenAI-compatible APIs (e.g., GPT-4, Claude via proxy).
- **OllamaClient (`ollama_client.py`):** Specific client for local Ollama models (e.g., Llama 3, Mistral).
- **AnthropicClient (`anthropic_client.py`):** Specific client for Anthropic's Claude models.

## 3. Interfaces (Contracts)
LLM client-related data structures are defined in `orion/contracts/llm_contracts.py`.

### 3.1 LLMClient Interface
- `async generate_text(request: LLMRequest) -> LLMResponse`: Sends a text generation request to the LLM.
- `async generate_embedding(text: str) -> EmbeddingResponse`: Generates embeddings for a given text.
- `async generate_vision_response(image_data: bytes, prompt: str) -> LLMResponse`: Sends a vision request to a multimodal LLM.

## 4. Dependencies
- **Internal:** `orion.contracts.llm_contracts`, `orion.contracts.router_contracts`
- **External:** `openai` (Python client), `httpx` (for Ollama), `anthropic` (Python client), `asyncio`.

## 5. Build Order & Verification (Phase 3 - M3.4)
1. Define LLM-related Pydantic models in `orion/contracts/llm_contracts.py`.
2. Implement the base `LLMClient` interface.
3. Implement `OpenAIClient` and `OllamaClient` with basic text generation.
4. Create a demo script (`examples/llm_client_demo.py`) to demonstrate text generation from both a local (mocked) and cloud (mocked) LLM.
5. Ensure unit tests for all LLM client modules pass.
"""
