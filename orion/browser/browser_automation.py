"""
ORION Browser Automation
=========================

Control web browsers using Playwright.

Features:
- Navigate to URLs
- Click, type, scroll
- Extract page content
- Take screenshots
- Fill forms
- Handle tabs

Usage:
    browser = BrowserAutomation()
    await browser.start()
    await browser.navigate("https://google.com")
    await browser.type("input[name=q]", "hello")
    await browser.click("button[type=submit]")
    content = await browser.get_content()
    await browser.stop()
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Browser automation using Playwright."""
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None
        self._context = None
    
    async def start(self, headless: bool = False) -> bool:
        """Start browser."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=headless)
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            self._page = await self._context.new_page()
            logger.info("Browser started")
            return True
        except Exception as e:
            logger.error("Failed to start browser: %s", e)
            return False
    
    async def stop(self):
        """Stop browser."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("Browser stopped")
        except Exception as e:
            logger.error("Failed to stop browser: %s", e)
    
    # ── Navigation ────────────────────────────────────────────
    
    async def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
            logger.info("Navigated to: %s", url)
            return True
        except Exception as e:
            logger.error("Navigation failed: %s", e)
            return False
    
    async def back(self):
        """Go back."""
        await self._page.go_back()
    
    async def forward(self):
        """Go forward."""
        await self._page.go_forward()
    
    async def reload(self):
        """Reload page."""
        await self._page.reload()
    
    async def get_url(self) -> str:
        """Get current URL."""
        return self._page.url
    
    async def get_title(self) -> str:
        """Get page title."""
        return await self._page.title()
    
    # ── Interaction ───────────────────────────────────────────
    
    async def click(self, selector: str) -> bool:
        """Click an element."""
        try:
            await self._page.click(selector)
            logger.info("Clicked: %s", selector)
            return True
        except Exception as e:
            logger.error("Click failed: %s", e)
            return False
    
    async def click_text(self, text: str) -> bool:
        """Click element by text."""
        try:
            await self._page.click(f"text={text}")
            return True
        except Exception as e:
            logger.error("Click text failed: %s", e)
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into element."""
        try:
            await self._page.fill(selector, text)
            logger.info("Typed into %s", selector)
            return True
        except Exception as e:
            logger.error("Type failed: %s", e)
            return False
    
    async def press_key(self, key: str):
        """Press a keyboard key."""
        await self._page.keyboard.press(key)
    
    async def scroll(self, direction: str = "down", amount: int = 3):
        """Scroll page."""
        delta = 300 * amount if direction == "down" else -300 * amount
        await self._page.mouse.wheel(0, delta)
    
    async def hover(self, selector: str):
        """Hover over element."""
        await self._page.hover(selector)
    
    # ── Content Extraction ────────────────────────────────────
    
    async def get_content(self) -> str:
        """Get page text content."""
        return await self._page.inner_text("body")
    
    async def get_html(self) -> str:
        """Get page HTML."""
        return await self._page.content()
    
    async def get_text(self, selector: str) -> str:
        """Get text of element."""
        try:
            return await self._page.inner_text(selector)
        except:
            return ""
    
    async def get_attribute(self, selector: str, attr: str) -> Optional[str]:
        """Get attribute of element."""
        try:
            return await self._page.get_attribute(selector, attr)
        except:
            return None
    
    async def query_selector_all(self, selector: str) -> List[str]:
        """Get all elements matching selector."""
        elements = await self._page.query_selector_all(selector)
        results = []
        for el in elements:
            text = await el.inner_text()
            results.append(text.strip())
        return results
    
    # ── Forms ─────────────────────────────────────────────────
    
    async def fill_form(self, fields: Dict[str, str]) -> bool:
        """Fill multiple form fields."""
        try:
            for selector, value in fields.items():
                await self._page.fill(selector, value)
            return True
        except Exception as e:
            logger.error("Fill form failed: %s", e)
            return False
    
    async def select_option(self, selector: str, value: str):
        """Select dropdown option."""
        await self._page.select_option(selector, value)
    
    async def check(self, selector: str):
        """Check a checkbox."""
        await self._page.check(selector)
    
    async def uncheck(self, selector: str):
        """Uncheck a checkbox."""
        await self._page.uncheck(selector)
    
    # ── Screenshots ───────────────────────────────────────────
    
    async def screenshot(self, path: str = "/tmp/orion_browser.png") -> str:
        """Take screenshot."""
        await self._page.screenshot(path=path)
        logger.info("Screenshot saved: %s", path)
        return path
    
    async def screenshot_element(self, selector: str, path: str = "/tmp/orion_element.png") -> str:
        """Screenshot specific element."""
        el = await self._page.query_selector(selector)
        if el:
            await el.screenshot(path=path)
        return path
    
    # ── Tabs ──────────────────────────────────────────────────
    
    async def new_tab(self, url: Optional[str] = None):
        """Open new tab."""
        page = await self._context.new_page()
        if url:
            await page.goto(url)
        self._page = page
    
    async def close_tab(self):
        """Close current tab."""
        await self._page.close()
    
    # ── Wait ──────────────────────────────────────────────────
    
    async def wait_for(self, selector: str, timeout: int = 10000):
        """Wait for element to appear."""
        await self._page.wait_for_selector(selector, timeout=timeout)
    
    async def wait_for_url(self, url_pattern: str, timeout: int = 10000):
        """Wait for URL to match."""
        await self._page.wait_for_url(url_pattern, timeout=timeout)
    
    async def wait_for_load(self):
        """Wait for page load."""
        await self._page.wait_for_load_state("domcontentloaded")
    
    # ── JavaScript ────────────────────────────────────────────
    
    async def execute_js(self, script: str) -> Any:
        """Execute JavaScript."""
        return await self._page.evaluate(script)
    
    # ── Info ──────────────────────────────────────────────────
    
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._browser is not None and self._browser.is_connected()
