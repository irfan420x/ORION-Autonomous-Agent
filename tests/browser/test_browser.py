"""
Tests for ORION Browser Automation (M5.3)
==========================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orion.browser.browser_automation import BrowserAutomation


@pytest.fixture
def browser():
    return BrowserAutomation()


class TestBrowserAutomation:
    def test_initialization(self, browser):
        assert browser._browser is None
        assert browser._page is None
        assert browser.is_running() is False

    @pytest.mark.asyncio
    async def test_start_mock(self, browser):
        with patch('playwright.async_api.async_playwright') as mock_pw:
            mock_playwright = AsyncMock()
            mock_pw.return_value = mock_playwright
            mock_browser = AsyncMock()
            mock_playwright.chromium.launch.return_value = mock_browser
            mock_context = AsyncMock()
            mock_browser.new_context.return_value = mock_context
            mock_page = AsyncMock()
            mock_context.new_page.return_value = mock_page
            mock_browser.is_connected.return_value = True
            
            result = await browser.start(headless=True)
            assert result is True

    @pytest.mark.asyncio
    async def test_navigate_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.goto = AsyncMock()
        result = await browser.navigate("https://example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_click_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.click = AsyncMock()
        result = await browser.click("button")
        assert result is True

    @pytest.mark.asyncio
    async def test_type_text_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.fill = AsyncMock()
        result = await browser.type_text("input", "hello")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_url_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.url = "https://example.com"
        url = await browser.get_url()
        assert url == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_title_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.title = AsyncMock(return_value="Test Page")
        title = await browser.get_title()
        assert title == "Test Page"

    @pytest.mark.asyncio
    async def test_get_content_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.inner_text = AsyncMock(return_value="Hello World")
        content = await browser.get_content()
        assert content == "Hello World"

    @pytest.mark.asyncio
    async def test_screenshot_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.screenshot = AsyncMock()
        path = await browser.screenshot("/tmp/test.png")
        assert path == "/tmp/test.png"

    @pytest.mark.asyncio
    async def test_fill_form_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.fill = AsyncMock()
        result = await browser.fill_form({"input": "value"})
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_js_mock(self, browser):
        browser._page = AsyncMock()
        browser._page.evaluate = AsyncMock(return_value=42)
        result = await browser.execute_js("return 42")
        assert result == 42
