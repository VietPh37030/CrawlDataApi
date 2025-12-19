"""
Main Crawler Module
High-level crawling functions including chapter content
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .browser import create_browser, BrowserManager
from .parsers import (
    parse_story_list,
    parse_story_detail,
    parse_chapter_content,
    get_pagination_info,
    extract_slug_from_url,
)
from .stealth import human_delay
from ..config import get_settings


class StoryCrawler:
    """
    Main crawler class for truyenfull.vision
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.base_url
    
    async def crawl_story(self, url: str, include_chapters: bool = False) -> Dict[str, Any]:
        """
        Crawl a single story
        
        Args:
            url: Story URL
            include_chapters: Whether to crawl chapter content (takes longer)
            
        Returns:
            Story data dict
        """
        async with create_browser() as browser:
            async with browser.new_page() as page:
                print(f"📖 Crawling story: {url}")
                
                # Navigate to story page
                await browser.navigate(page, url)
                html = await browser.get_page_content(page)
                
                # Parse story details (first page)
                story = parse_story_detail(html, url)
                
                # 🔥 FIX: Crawl ALL pages of chapter list
                all_chapters = story.get("chapters", [])
                
                # Check if there are more pages
                from .parsers import get_pagination_info
                pagination = get_pagination_info(html)
                total_pages = pagination.get("total_pages", 1)
                
                if total_pages > 1:
                    print(f"📄 Found {total_pages} pages of chapters, crawling all...")
                    
                    for page_num in range(2, total_pages + 1):
                        try:
                            # Build pagination URL (e.g., /ten-truyen/trang-2/)
                            page_url = url.rstrip("/") + f"/trang-{page_num}/"
                            print(f"  📃 Crawling page {page_num}: {page_url}")
                            
                            await browser.navigate(page, page_url)
                            page_html = await browser.get_page_content(page)
                            
                            # Parse chapters from this page
                            from bs4 import BeautifulSoup
                            from .parsers import parse_chapter_list
                            soup = BeautifulSoup(page_html, "lxml")
                            page_chapters = parse_chapter_list(soup)
                            
                            all_chapters.extend(page_chapters)
                            print(f"  ✅ Found {len(page_chapters)} chapters on page {page_num}")
                            
                        except Exception as e:
                            print(f"  ⚠️ Error crawling page {page_num}: {e}")
                            continue
                
                story["chapters"] = all_chapters
                story["total_chapters"] = len(all_chapters)
                
                print(f"📚 Total chapters found: {len(all_chapters)}")
                
                # Optionally crawl chapter content
                if include_chapters and story.get("chapters"):
                    print(f"📚 Crawling {len(story['chapters'])} chapters...")
                    story["chapters"] = await self._crawl_chapters(
                        browser, page, story["chapters"]
                    )
                
                return story
    
    async def crawl_single_chapter(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single chapter's content
        
        Args:
            url: Chapter URL
            
        Returns:
            Chapter data with content
        """
        async with create_browser() as browser:
            async with browser.new_page() as page:
                try:
                    await browser.navigate(page, url)
                    html = await browser.get_page_content(page)
                    chapter = parse_chapter_content(html, url)
                    return chapter
                except Exception as e:
                    print(f"Error crawling chapter {url}: {e}")
                    return {"content": None, "error": str(e)}
    
    async def _crawl_chapters(
        self, 
        browser: BrowserManager, 
        page, 
        chapters: List[Dict[str, Any]],
        max_chapters: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl chapter content for a list of chapters
        """
        if max_chapters:
            chapters = chapters[:max_chapters]
        
        crawled_chapters = []
        
        for i, chapter in enumerate(chapters):
            try:
                print(f"  📄 Chapter {i+1}/{len(chapters)}: {chapter.get('title', 'Unknown')}")
                
                await browser.navigate(page, chapter["source_url"])
                html = await browser.get_page_content(page)
                
                chapter_data = parse_chapter_content(html, chapter["source_url"])
                chapter_data["chapter_number"] = chapter.get("chapter_number", i + 1)
                
                crawled_chapters.append(chapter_data)
                
                # Extra delay between chapters to be polite
                await human_delay(2, 5)
                
            except Exception as e:
                print(f"  ❌ Error crawling chapter: {e}")
                crawled_chapters.append({
                    "chapter_number": chapter.get("chapter_number", i + 1),
                    "title": chapter.get("title", ""),
                    "source_url": chapter.get("source_url", ""),
                    "content": None,
                    "error": str(e),
                })
        
        return crawled_chapters
    
    async def crawl_story_list(
        self, 
        list_url: str, 
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Crawl story listing page(s)
        
        Args:
            list_url: URL of listing page (e.g., /danh-sach/truyen-hot/)
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of story basic info
        """
        all_stories = []
        
        async with create_browser() as browser:
            async with browser.new_page() as page:
                current_url = list_url
                
                for page_num in range(max_pages):
                    print(f"📃 Crawling list page {page_num + 1}: {current_url}")
                    
                    await browser.navigate(page, current_url)
                    html = await browser.get_page_content(page)
                    
                    # Parse stories on this page
                    stories = parse_story_list(html)
                    all_stories.extend(stories)
                    
                    print(f"  Found {len(stories)} stories")
                    
                    # Get pagination info
                    pagination = get_pagination_info(html)
                    
                    if pagination["next_page_url"] and page_num < max_pages - 1:
                        current_url = pagination["next_page_url"]
                        await human_delay(3, 6)
                    else:
                        break
        
        return all_stories
    
    async def crawl_hot_stories(self, max_pages: int = 2) -> List[Dict[str, Any]]:
        """Crawl hot/trending stories"""
        return await self.crawl_story_list(
            f"{self.base_url}/danh-sach/truyen-hot/", 
            max_pages
        )
    
    async def crawl_new_stories(self, max_pages: int = 2) -> List[Dict[str, Any]]:
        """Crawl newly updated stories"""
        return await self.crawl_story_list(
            f"{self.base_url}/danh-sach/truyen-moi/",
            max_pages
        )
    
    async def crawl_completed_stories(self, max_pages: int = 2) -> List[Dict[str, Any]]:
        """Crawl completed stories"""
        return await self.crawl_story_list(
            f"{self.base_url}/danh-sach/truyen-full/",
            max_pages
        )


# Convenience function for standalone usage
async def crawl_story(url: str, include_chapters: bool = False) -> Dict[str, Any]:
    """
    Convenience function to crawl a single story
    """
    crawler = StoryCrawler()
    return await crawler.crawl_story(url, include_chapters)


async def crawl_stories_list(category: str = "hot", max_pages: int = 1) -> List[Dict[str, Any]]:
    """
    Convenience function to crawl story lists
    """
    crawler = StoryCrawler()
    
    if category == "hot":
        return await crawler.crawl_hot_stories(max_pages)
    elif category == "new":
        return await crawler.crawl_new_stories(max_pages)
    elif category == "completed":
        return await crawler.crawl_completed_stories(max_pages)
    else:
        return await crawler.crawl_story_list(category, max_pages)
