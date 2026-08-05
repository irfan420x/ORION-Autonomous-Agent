from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal

class UIElementInfo(BaseModel):
    element_id: str = Field(..., description="Unique identifier for the UI element (e.g., accessibility ID)")
    name: Optional[str] = Field(None, description="Name or text content of the element")
    role: Optional[str] = Field(None, description="Role of the element (e.g., button, textbox, menu)")
    bounds: Dict[str, int] = Field(..., description="x, y, width, height of the element on screen")
    is_enabled: bool = Field(..., description="True if the element is enabled for interaction")
    is_visible: bool = Field(..., description="True if the element is visible on screen")
    parent_id: Optional[str] = Field(None, description="ID of the parent UI element")

class ClickAction(BaseModel):
    element_id: Optional[str] = Field(None, description="ID of the element to click")
    x: Optional[int] = Field(None, description="X coordinate for click if element_id is not used")
    y: Optional[int] = Field(None, description="Y coordinate for click if element_id is not used")
    button: Literal["left", "right", "middle"] = Field("left", description="Mouse button to click")
    clicks: int = Field(1, description="Number of clicks")

class TypeAction(BaseModel):
    element_id: Optional[str] = Field(None, description="ID of the element to type into")
    text: str = Field(..., description="Text to type")
    press_enter: bool = Field(False, description="Whether to press Enter after typing")

class FindElementRequest(BaseModel):
    selector: str = Field(..., description="Selector to find the element (e.g., text, accessibility ID)")
    timeout: int = Field(10, description="Timeout in seconds to wait for the element")

class GUIActionResult(BaseModel):
    success: bool = Field(..., description="True if the GUI action was successful")
    message: Optional[str] = Field(None, description="Detailed message about the action result")
    element_info: Optional[UIElementInfo] = Field(None, description="Information about the element involved in the action")
