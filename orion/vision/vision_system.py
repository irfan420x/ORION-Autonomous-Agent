"""
ORION Vision System
===================

Advanced vision capabilities for ORION:
- Screenshot analysis with element detection
- OCR (text extraction from images)
- UI element detection and classification
- Image understanding via LLM

Uses: PIL, pytesseract, OpenCV (optional), LLM vision API
"""

import logging
import os
import base64
import json
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionSystem:
    """
    Vision system for ORION - screenshot analysis, OCR, UI detection.
    """
    
    def __init__(self, llm_client=None):
        self._llm = llm_client
        self._screenshot_dir = "/tmp/orion_vision"
        os.makedirs(self._screenshot_dir, exist_ok=True)
    
    # ── Screenshot Capture ────────────────────────────────────
    
    def capture_screen(self, output_path: Optional[str] = None) -> Optional[str]:
        """Capture full screen screenshot."""
        if output_path is None:
            output_path = os.path.join(self._screenshot_dir, "screen.png")
        
        try:
            import subprocess
            subprocess.run(['scrot', output_path], check=True, capture_output=True)
            logger.info("Screenshot captured: %s", output_path)
            return output_path
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int, 
                       output_path: Optional[str] = None) -> Optional[str]:
        """Capture a specific region of the screen."""
        if output_path is None:
            output_path = os.path.join(self._screenshot_dir, "region.png")
        
        try:
            import subprocess
            # Use scrot with selection, or import for region
            subprocess.run(
                ['import', '-window', 'root', '-crop', f'{width}x{height}+{x}+{y}', output_path],
                check=True, capture_output=True
            )
            return output_path
        except Exception as e:
            logger.error("Region capture failed: %s", e)
            return None
    
    # ── OCR (Text Extraction) ─────────────────────────────────
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='eng+ben')  # English + Bengali
            logger.info("OCR extracted %d chars from %s", len(text), image_path)
            return text.strip()
        except ImportError:
            logger.warning("pytesseract not installed, using fallback")
            return self._fallback_ocr(image_path)
        except Exception as e:
            logger.error("OCR failed: %s", e)
            return ""
    
    def _fallback_ocr(self, image_path: str) -> str:
        """Fallback OCR using LLM vision if available."""
        if self._llm:
            return self._analyze_with_llm(image_path, "Extract all text from this image")
        return ""
    
    # ── UI Element Detection ──────────────────────────────────
    
    def detect_elements(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect UI elements in screenshot.
        Returns list of elements with type, position, text.
        """
        try:
            from PIL import Image
            import subprocess
            
            # Get image dimensions
            img = Image.open(image_path)
            width, height = img.size
            
            # Use OCR to find text elements
            text_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            elements = []
            for i in range(len(text_data['text'])):
                text = text_data['text'][i].strip()
                if text and int(text_data['conf'][i]) > 30:
                    elements.append({
                        'type': 'text',
                        'text': text,
                        'x': text_data['left'][i],
                        'y': text_data['top'][i],
                        'width': text_data['width'][i],
                        'height': text_data['height'][i],
                        'confidence': int(text_data['conf'][i]),
                    })
            
            logger.info("Detected %d elements in %s", len(elements), image_path)
            return elements
            
        except ImportError:
            logger.warning("pytesseract not installed")
            return []
        except Exception as e:
            logger.error("Element detection failed: %s", e)
            return []
    
    def find_element(self, image_path: str, text: str) -> Optional[Dict[str, Any]]:
        """Find a specific element by text."""
        elements = self.detect_elements(image_path)
        for elem in elements:
            if text.lower() in elem['text'].lower():
                return elem
        return None
    
    def find_button(self, image_path: str, label: str) -> Optional[Tuple[int, int]]:
        """Find a button by label and return center coordinates."""
        elem = self.find_element(image_path, label)
        if elem:
            center_x = elem['x'] + elem['width'] // 2
            center_y = elem['y'] + elem['height'] // 2
            return (center_x, center_y)
        return None
    
    # ── Image Analysis (LLM-powered) ─────────────────────────
    
    def analyze_screenshot(self, image_path: str, question: str = "What is shown?") -> str:
        """Analyze screenshot using LLM vision."""
        return self._analyze_with_llm(image_path, question)
    
    def describe_ui(self, image_path: str) -> str:
        """Describe the UI elements in the screenshot."""
        return self._analyze_with_llm(
            image_path,
            "Describe all UI elements, buttons, text fields, and their positions in detail"
        )
    
    def find_clickable(self, image_path: str) -> List[Dict[str, Any]]:
        """Find all clickable elements in screenshot."""
        response = self._analyze_with_llm(
            image_path,
            "List all clickable elements (buttons, links, icons) with their approximate positions"
        )
        # Parse response for clickable elements
        return self._parse_clickable_response(response)
    
    def _analyze_with_llm(self, image_path: str, prompt: str) -> str:
        """Analyze image using LLM vision API."""
        if not self._llm:
            return "LLM not available for vision analysis"
        
        try:
            # Read image and encode to base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Call LLM with vision
            import asyncio
            
            async def call_vision():
                # Check if LLM supports vision
                if hasattr(self._llm, 'chat_with_vision'):
                    return await self._llm.chat_with_vision(
                        prompt=prompt,
                        image_data=image_data,
                    )
                else:
                    # Fallback: use regular chat with image description
                    return await self._llm.chat(
                        f"{prompt}\n[Image: {image_path}]",
                    )
            
            return asyncio.run(call_vision())
            
        except Exception as e:
            logger.error("LLM vision analysis failed: %s", e)
            return f"Analysis failed: {e}"
    
    def _parse_clickable_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response for clickable elements."""
        elements = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line.lower() for kw in ['button', 'click', 'link', 'icon']):
                elements.append({
                    'type': 'clickable',
                    'description': line,
                    'text': line,
                })
        return elements
    
    # ── Image Comparison ──────────────────────────────────────
    
    def compare_images(self, img1_path: str, img2_path: str) -> Dict[str, Any]:
        """Compare two images and return differences."""
        try:
            from PIL import Image
            import numpy as np
            
            img1 = Image.open(img1_path).convert('RGB')
            img2 = Image.open(img2_path).convert('RGB')
            
            # Resize to same size if different
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            
            # Convert to numpy arrays
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Calculate difference
            diff = np.abs(arr1.astype(int) - arr2.astype(int))
            mean_diff = diff.mean()
            max_diff = diff.max()
            
            # Find changed regions
            changed_pixels = (diff > 30).any(axis=2)
            change_percentage = changed_pixels.sum() / changed_pixels.size * 100
            
            return {
                'identical': mean_diff < 5,
                'mean_difference': float(mean_diff),
                'max_difference': int(max_diff),
                'change_percentage': round(change_percentage, 2),
                'similarity': round(100 - change_percentage, 2),
            }
            
        except ImportError:
            return {'error': 'numpy/PIL not installed'}
        except Exception as e:
            return {'error': str(e)}
    
    # ── Color Analysis ────────────────────────────────────────
    
    def get_dominant_colors(self, image_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """Get dominant colors in image."""
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path).convert('RGB')
            img = img.resize((100, 100))  # Reduce for speed
            pixels = np.array(img).reshape(-1, 3)
            
            # Simple color quantization
            from collections import Counter
            pixel_tuples = [tuple(p) for p in pixels[::10]]  # Sample every 10th
            color_counts = Counter(pixel_tuples)
            
            return [color for color, _ in color_counts.most_common(num_colors)]
            
        except ImportError:
            return []
        except Exception as e:
            logger.error("Color analysis failed: %s", e)
            return []
    
    # ── Info ──────────────────────────────────────────────────
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get image metadata."""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            return {
                'path': image_path,
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size': os.path.getsize(image_path),
            }
        except Exception as e:
            return {'error': str(e)}
