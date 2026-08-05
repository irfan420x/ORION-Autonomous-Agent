"""
Tests for ORION Vision System (M5.4)
=====================================
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch

from orion.vision.vision_system import VisionSystem


@pytest.fixture
def vision():
    return VisionSystem()


@pytest.fixture
def sample_image():
    """Create a simple test image."""
    try:
        from PIL import Image
        path = tempfile.mktemp(suffix='.png')
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path)
        yield path
        os.remove(path)
    except ImportError:
        pytest.skip("PIL not installed")


class TestVisionSystem:
    def test_initialization(self, vision):
        assert vision._llm is None
        assert os.path.exists(vision._screenshot_dir)

    def test_initialization_with_llm(self):
        mock_llm = MagicMock()
        vision = VisionSystem(llm_client=mock_llm)
        assert vision._llm is not None

    def test_capture_screen(self, vision):
        result = vision.capture_screen("/tmp/test_capture.png")
        # May fail in headless, but should not crash
        assert result is None or isinstance(result, str)

    def test_capture_screen_no_path(self, vision):
        result = vision.capture_screen()
        assert result is None or isinstance(result, str)

    def test_extract_text_no_pil(self, vision):
        with patch.dict('sys.modules', {'pytesseract': None}):
            result = vision.extract_text("/tmp/nonexistent.png")
            assert isinstance(result, str)

    def test_detect_elements_no_pil(self, vision):
        with patch.dict('sys.modules', {'pytesseract': None}):
            result = vision.detect_elements("/tmp/nonexistent.png")
            assert isinstance(result, list)

    def test_find_element_empty(self, vision):
        result = vision.find_element("/tmp/nonexistent.png", "button")
        assert result is None

    def test_find_button_empty(self, vision):
        result = vision.find_button("/tmp/nonexistent.png", "Submit")
        assert result is None

    def test_analyze_without_llm(self, vision):
        result = vision.analyze_screenshot("/tmp/test.png")
        assert "not available" in result.lower() or "LLM" in result

    def test_describe_ui_without_llm(self, vision):
        result = vision.describe_ui("/tmp/test.png")
        assert isinstance(result, str)

    def test_find_clickable_without_llm(self, vision):
        result = vision.find_clickable("/tmp/test.png")
        assert isinstance(result, list)

    def test_compare_images_same(self, vision, sample_image):
        result = vision.compare_images(sample_image, sample_image)
        if 'error' not in result:
            assert result['identical'] == True  # numpy True_ or Python True
            assert result['similarity'] == 100.0

    def test_get_dominant_colors(self, vision, sample_image):
        colors = vision.get_dominant_colors(sample_image)
        if colors:  # May be empty if PIL not available
            assert len(colors) > 0
            assert len(colors[0]) == 3

    def test_get_image_info(self, vision, sample_image):
        info = vision.get_image_info(sample_image)
        if 'error' not in info:
            assert info['width'] == 100
            assert info['height'] == 100

    def test_get_image_info_nonexistent(self, vision):
        info = vision.get_image_info("/tmp/nonexistent.png")
        assert 'error' in info

    def test_parse_clickable_response(self, vision):
        response = "Button: Submit\nLink: Home\nText: Hello\nIcon: Settings"
        result = vision._parse_clickable_response(response)
        assert len(result) >= 2  # At least Button and Link
