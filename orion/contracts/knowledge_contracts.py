from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from orion.contracts.memory_contracts import Document, SearchResult

class KnowledgeItem(BaseModel):
    item_id: str = Field(..., description="Unique identifier for the knowledge item")
    content: str = Field(..., description="The content of the knowledge item")
    source: str = Field(..., description="Source of the knowledge (e.g., file path, URL, user input)")
    timestamp: float = Field(..., description="Unix timestamp of when the knowledge was acquired")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the knowledge item")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

class GraphEntity(BaseModel):
    entity_id: str = Field(..., description="Unique identifier for the entity")
    entity_type: str = Field(..., description="Type of the entity (e.g., 'Person', 'Project', 'Tool')")
    name: str = Field(..., description="Name or label of the entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key-value properties of the entity")

class GraphRelationship(BaseModel):
    source_entity_id: str = Field(..., description="ID of the source entity")
    target_entity_id: str = Field(..., description="ID of the target entity")
    relationship_type: str = Field(..., description="Type of relationship (e.g., 'HAS_TOOL', 'WORKS_ON', 'DEPENDS_ON')")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Properties of the relationship")

class GraphQueryResult(BaseModel):
    query: str = Field(..., description="The original graph query")
    results: List[Dict[str, Any]] = Field(..., description="List of results from the graph query")
    visualization_data: Optional[Dict[str, Any]] = Field(None, description="Data for visualizing the query results")

class IndexingJob(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the indexing job")
    target_path: str = Field(..., description="Path to the directory or file to index")
    status: str = Field("PENDING", description="Current status of the indexing job")
    start_time: float = Field(..., description="Unix timestamp of job start")
    end_time: Optional[float] = Field(None, description="Unix timestamp of job end")
    indexed_documents: List[str] = Field(default_factory=list, description="List of document IDs that were indexed")
