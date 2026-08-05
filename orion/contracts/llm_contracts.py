from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class EmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="The generated embedding vector")
    model_id: str = Field(..., description="ID of the model that generated the embedding")
    input_tokens: int = Field(..., description="Number of input tokens used")
    cost: float = Field(..., description="Estimated cost of the request in USD")

class VisionRequest(BaseModel):
    image_data_base64: str = Field(..., description="Base64 encoded image data")
    prompt: str = Field(..., description="The prompt for the vision model")
    model_id: Optional[str] = Field(None, description="Preferred model ID, if any")
    detail: Literal["auto", "low", "high"] = Field("auto", description="Detail level for vision models")

class VisionResponse(BaseModel):
    model_id: str = Field(..., description="ID of the model that generated the response")
    text: str = Field(..., description="Generated text response from vision model")
    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    cost: float = Field(..., description="Estimated cost of the request in USD")

