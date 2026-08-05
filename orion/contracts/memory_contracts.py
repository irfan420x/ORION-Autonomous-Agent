from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class MemoryItem(BaseModel):
    key: str = Field(..., description="Unique key for the memory item")
    value: Any = Field(..., description="The value stored in memory")
    timestamp: float = Field(..., description="Unix timestamp of when the item was stored")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata for the memory item")

class Document(BaseModel):
    doc_id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="The textual content of the document")
    metadata: Dict[str, Any] = Field({}, description="Metadata associated with the document")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the document content")

class SearchResult(BaseModel):
    doc_id: str = Field(..., description="Identifier of the matched document")
    content: str = Field(..., description="Content of the matched document")
    metadata: Dict[str, Any] = Field({}, description="Metadata of the matched document")
    score: float = Field(..., description="Relevance score of the search result")
