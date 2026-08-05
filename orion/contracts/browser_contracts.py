from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BrowserContextInfo(BaseModel):
    context_id: str = Field(..., description="Unique identifier for the browser context")
    browser_type: str = Field(..., description="Type of browser (e.g., chromium, firefox, webkit)")
    headless: bool = Field(..., description="True if browser is running in headless mode")
    user_agent: str = Field(..., description="User agent string of the browser")

class PageInfo(BaseModel):
    page_id: str = Field(..., description="Unique identifier for the page")
    context_id: str = Field(..., description="ID of the browser context this page belongs to")
    url: str = Field(..., description="Current URL of the page")
    title: str = Field(..., description="Title of the page")
    is_closed: bool = Field(False, description="True if the page is closed")

class ElementInfo(BaseModel):
    selector: str = Field(..., description="CSS selector or XPath used to locate the element")
    text_content: Optional[str] = Field(None, description="Text content of the element")
    tag_name: Optional[str] = Field(None, description="HTML tag name of the element")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs of element attributes")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="x, y, width, height of the element on screen")

class WebAction(BaseModel):
    action_type: str = Field(..., description="Type of web action (e.g., 'click', 'fill', 'goto')")
    page_id: str = Field(..., description="ID of the page to perform the action on")
    selector: Optional[str] = Field(None, description="CSS selector or XPath for the target element")
    value: Optional[str] = Field(None, description="Value to input for 'fill' action")
    url: Optional[str] = Field(None, description="URL for 'goto' action")

class WebActionResult(BaseModel):
    success: bool = Field(..., description="True if the web action was successful")
    message: Optional[str] = Field(None, description="Detailed message about the action result")
    output: Optional[str] = Field(None, description="Output from the action (e.g., extracted text)")
