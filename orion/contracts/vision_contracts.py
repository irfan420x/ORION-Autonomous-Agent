from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BoundingBox(BaseModel):
    x: int = Field(..., description="X coordinate of the top-left corner")
    y: int = Field(..., description="Y coordinate of the top-left corner")
    width: int = Field(..., description="Width of the bounding box")
    height: int = Field(..., description="Height of the bounding box")

class OCRResult(BaseModel):
    text: str = Field(..., description="Extracted text")
    bounding_box: BoundingBox = Field(..., description="Bounding box of the extracted text")
    confidence: float = Field(..., description="Confidence score of the OCR result")

class DetectedUIElement(BaseModel):
    element_id: str = Field(..., description="Unique identifier for the UI element")
    type: str = Field(..., description="Type of UI element (e.g., button, textbox, image)")
    text: Optional[str] = Field(None, description="Text content of the UI element")
    bounding_box: BoundingBox = Field(..., description="Bounding box of the UI element")
    confidence: float = Field(..., description="Confidence score of the detection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the element")

class VisionAnalysisResult(BaseModel):
    description: str = Field(..., description="Natural language description of the image content")
    detected_objects: List[DetectedUIElement] = Field(default_factory=list, description="List of detected UI elements or objects")
    ocr_results: List[OCRResult] = Field(default_factory=list, description="List of OCR results from the image")
    raw_llm_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from the Vision LLM")
