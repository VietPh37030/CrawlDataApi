"""
Playwright Browser Manager
Handles browser lifecycle and page creation with stealth mode
"""
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .stealth import get_stealth_context_options, inject_stealth_scripts, simulate_human_behavior, human_delay


class BrowserManager:
    """
    Manages Playwright browser instance with stealth configuration
    """
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def start(self) -> None:
        """Initialize browser"""
        self._playwright = await async_playwright().start()
        
        # Launch Chromium with stealth args + RENDER OPTIMIZATION (512MB RAM)
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",  # Critical for Render
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--window-size=1280,720",  # Reduced from 1920x1080
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--metrics-recording-only",
                "--single-process",  # Less RAM, slightly slower
            ]
        )
        
        # Create context with stealth options
        context_options = get_stealth_context_options()
        self._context = await self._browser.new_context(**context_options)
        
        # Block unnecessary resources to speed up crawling
        await self._context.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2}", 
                                   lambda route: route.abort())
    
    async def stop(self) -> None:
        """Close browser and cleanup"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    @asynccontextmanager
    async def new_page(self):
        """Create a new page with stealth scripts"""
        if not self._context:
            await self.start()
        
        page = await self._context.new_page()
        
        # Inject stealth scripts
        await inject_stealth_scripts(page)
        
        try:
            yield page
        finally:
            await page.close()
    
    async def navigate(self, page: Page, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate to URL with human-like behavior"""
        # Add human delay before navigation
        await human_delay(1, 3)
        
        await page.goto(url, wait_until=wait_until, timeout=30000)
        
        # Simulate human behavior after page load
        await simulate_human_behavior(page)
        
        # Additional delay after navigation
        await human_delay(2, 4)
    
    async def get_page_content(self, page: Page) -> str:
        """Get page HTML content"""
        return await page.content()


# Context manager for easy usage
@asynccontextmanager
async def create_browser():
    """
    Context manager to create and manage browser instance
    
    Usage:
        async with create_browser() as browser:
            async with browser.new_page() as page:
                await browser.navigate(page, url)
                content = await browser.get_page_content(page)
    """
    browser = BrowserManager()
    try:
        await browser.start()
        yield browser
    finally:
        await browser.stop()
