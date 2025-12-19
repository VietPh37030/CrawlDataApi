#!/usr/bin/env python
"""Test crawl with httpx only (no Playwright)"""
import asyncio
import sys
sys.path.append('.')

async def test():
    import httpx
    from app.crawler.parsers import parse_story_detail, get_pagination_info, parse_chapter_list
    from bs4 import BeautifulSoup
    
    url = "https://truyenfull.vision/tam-quoc-dien-nghia/"
    print(f"Testing with HTTPX: {url}\n")
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Page 1
        print("Fetching page 1...")
        response = await client.get(url)
        html = response.text
        
        # Parse story
        story = parse_story_detail(html, url)
        print(f"Title: {story['title']}")
        print(f"Chapters on page 1: {len(story['chapters'])}")
        
        # Check pagination
        pagination = get_pagination_info(html)
        total_pages = pagination['total_pages']
        print(f"Total pages: {total_pages}\n")
        
        all_chapters = story['chapters']
        
        # Fetch other pages
        if total_pages > 1:
            for page_num in range(2, total_pages + 1):
                page_url = url.rstrip("/") + f"/trang-{page_num}/#list-chapter"
                print(f"Fetching page {page_num}: {page_url}")
                
                response = await client.get(page_url)
                soup = BeautifulSoup(response.text, "lxml")
                page_chapters = parse_chapter_list(soup)
                
                all_chapters.extend(page_chapters)
                print(f"  -> Found {len(page_chapters)} chapters")
        
        print(f"\n{'='*50}")
        print(f"✅ TOTAL CHAPTERS: {len(all_chapters)}")
        print(f"Cover: {story.get('cover_url', 'N/A')[:60]}...")

if __name__ == "__main__":
    asyncio.run(test())
