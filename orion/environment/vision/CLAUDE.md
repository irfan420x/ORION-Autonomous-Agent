"""# CLAUDE.md - Vision Subsystem

## 1. Overview
ORION's Vision Subsystem provides the agent with the ability to 
interpret and understand visual information from the screen. This includes OCR, UI element detection, and visual reasoning, which are critical for GUI automation and general environmental awareness.

## 2. Components
- **VisionEngine (`vision_engine.py`):** The core component that orchestrates various vision tasks, including screenshot capture, image processing, and integration with specialized vision models.
- **OCREngine (`ocr_engine.py`):** Extracts text from images using local (e.g., EasyOCR) or cloud-based (e.g., Google Vision API) OCR solutions.
- **UIDetector (`ui_detector.py`):** Identifies and localizes UI elements (buttons, text fields, icons) on the screen using computer vision models (e.g., YOLO).
- **VisualReasoning (`visual_reasoning.py`):** Interfaces with Vision LLMs to perform high-level interpretation of visual scenes.

## 3. Interfaces (Contracts)
Vision-related data structures are defined in `orion/contracts/vision_contracts.py`.

### 3.1 VisionEngine Interface
- `async capture_screenshot(region: Optional[Dict[str, int]] = None) -> bytes`: Captures a screenshot of the entire screen or a specified region.
- `async analyze_image(image_data: bytes, prompt: str) -> VisionResponse`: Sends an image to a Vision LLM for analysis.

### 3.2 OCREngine Interface
- `async perform_ocr(image_data: bytes) -> List[OCRResult]`: Performs OCR on an image and returns detected text with bounding boxes.

### 3.3 UIDetector Interface
- `async detect_ui_elements(image_data: bytes) -> List[UIElementInfo]`: Detects and returns information about UI elements in an image.

## 4. Dependencies
- **Internal:** `orion.contracts.vision_contracts`, `orion.contracts.llm_contracts`, `orion.core.communication.event_bus`, `orion.intelligence.router.model_router`
- **External:** `Pillow`, `OpenCV`, `EasyOCR`, `ultralytics` (for YOLO), `asyncio`.

## 5. Build Order & Verification (Phase 5 - M5.4)
1. Define vision-related Pydantic models in `orion/contracts/vision_contracts.py`.
2. Implement `OCREngine` with basic text extraction from images.
3. Implement `UIDetector` (initially with simple image matching, later with YOLO integration).
4. Implement `VisionEngine` to capture screenshots and integrate with OCR/UI detection.
5. Create a demo script (`examples/vision_engine_demo.py`) to demonstrate screenshot capture, OCR, and basic UI element detection.
6. Ensure unit tests for all Vision modules pass.
