"""
Anti-Detection & Stealth Module
Implements strategies to avoid bot detection
"""
import random
import asyncio
from typing import Optional
from ..config import USER_AGENTS, get_settings


def get_random_user_agent() -> str:
    """Get a random User-Agent string"""
    return random.choice(USER_AGENTS)


def get_random_delay() -> float:
    """Get random delay between requests"""
    settings = get_settings()
    return random.uniform(settings.crawl_delay_min, settings.crawl_delay_max)


async def human_delay(min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
    """Add human-like random delay"""
    settings = get_settings()
    min_s = min_seconds or settings.crawl_delay_min
    max_s = max_seconds or settings.crawl_delay_max
    delay = random.uniform(min_s, max_s)
    await asyncio.sleep(delay)


def get_stealth_context_options() -> dict:
    """Get browser context options for stealth mode"""
    # Random viewport sizes (common resolutions)
    viewports = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1280, "height": 720},
    ]
    
    viewport = random.choice(viewports)
    user_agent = get_random_user_agent()
    
    return {
        "user_agent": user_agent,
        "viewport": viewport,
        "locale": "vi-VN",
        "timezone_id": "Asia/Ho_Chi_Minh",
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 10.8231, "longitude": 106.6297},  # Ho Chi Minh City
        "color_scheme": random.choice(["light", "dark"]),
        "device_scale_factor": random.choice([1, 1.25, 1.5, 2]),
        "has_touch": False,
        "is_mobile": False,
        "java_script_enabled": True,
        "accept_downloads": False,
    }


async def inject_stealth_scripts(page) -> None:
    """
    Inject stealth scripts to hide automation indicators
    """
    # Hide webdriver property
    await page.add_init_script("""
        // Overwrite the `navigator.webdriver` property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Overwrite the `navigator.plugins` property to make it seem like there are plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Overwrite the `navigator.languages` property
        Object.defineProperty(navigator, 'languages', {
            get: () => ['vi-VN', 'vi', 'en-US', 'en']
        });
        
        // Pass the Chrome Test
        window.chrome = {
            runtime: {}
        };
        
        // Pass Permissions Test
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)


def get_random_mouse_movements() -> list:
    """Generate random mouse movement coordinates"""
    movements = []
    x, y = random.randint(100, 800), random.randint(100, 600)
    
    for _ in range(random.randint(3, 7)):
        x += random.randint(-50, 50)
        y += random.randint(-30, 30)
        x = max(0, min(x, 1920))
        y = max(0, min(y, 1080))
        movements.append((x, y))
    
    return movements


async def simulate_human_behavior(page) -> None:
    """Simulate human-like behavior to avoid detection"""
    # Random scroll
    scroll_amount = random.randint(100, 300)
    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    
    await asyncio.sleep(random.uniform(0.3, 0.8))
    
    # Random mouse movement
    movements = get_random_mouse_movements()
    for x, y in movements:
        try:
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        except:
            pass
