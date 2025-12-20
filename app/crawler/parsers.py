"""
HTML Parsers for truyenfull.vision
Extracts story and chapter data from HTML pages
"""
import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://truyenfull.vision"


def extract_slug_from_url(url: str) -> str:
    """Extract story slug from URL"""
    # https://truyenfull.vision/tam-quoc-dien-nghia/ -> tam-quoc-dien-nghia
    url = url.rstrip("/")
    parts = url.split("/")
    return parts[-1] if parts else ""


def parse_story_list(html: str) -> List[Dict[str, Any]]:
    """
    Parse story listing page (e.g., /danh-sach/truyen-moi/)
    Returns list of story basic info
    """
    soup = BeautifulSoup(html, "lxml")
    stories = []
    
    # Find story items (adjust selector based on actual HTML structure)
    story_items = soup.select(".list-truyen .row, .list-truyen-item")
    
    for item in story_items:
        try:
            # Get title and URL
            title_elem = item.select_one("h3.truyen-title a, .truyen-title a")
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            url = urljoin(BASE_URL, title_elem.get("href", ""))
            slug = extract_slug_from_url(url)
            
            # Get author
            author_elem = item.select_one(".author, span.author")
            author = author_elem.get_text(strip=True) if author_elem else None
            
            # Get latest chapter
            chapter_elem = item.select_one(".text-info a, .chapter-text")
            latest_chapter = chapter_elem.get_text(strip=True) if chapter_elem else None
            
            stories.append({
                "title": title,
                "slug": slug,
                "source_url": url,
                "author": author,
                "latest_chapter": latest_chapter,
            })
        except Exception as e:
            print(f"Error parsing story item: {e}")
            continue
    
    return stories


def parse_story_detail(html: str, url: str) -> Dict[str, Any]:
    """
    Parse story detail page
    Returns full story info including chapter list
    """
    soup = BeautifulSoup(html, "lxml")
    
    story = {
        "slug": extract_slug_from_url(url),
        "source_url": url,
        "title": "",
        "author": None,
        "description": None,
        "genres": [],
        "status": "ongoing",
        "total_chapters": 0,
        "cover_url": None,
        "chapters": [],
    }
    
    # Title
    title_elem = soup.select_one("h3.title, .title")
    if title_elem:
        story["title"] = title_elem.get_text(strip=True)
    
    # Cover image
    cover_elem = soup.select_one(".book img, .info-holder img")
    if cover_elem:
        story["cover_url"] = urljoin(BASE_URL, cover_elem.get("src", ""))
    
    # Info section
    info_section = soup.select_one(".info, .info-holder")
    if info_section:
        # Author
        author_elem = info_section.select_one('a[itemprop="author"], .author a')
        if author_elem:
            story["author"] = author_elem.get_text(strip=True)
        
        # Genres
        genre_elems = info_section.select('a[itemprop="genre"], .genre a')
        story["genres"] = [g.get_text(strip=True) for g in genre_elems]
        
        # Status
        status_elem = info_section.select_one(".text-success, .text-primary")
        if status_elem:
            status_text = status_elem.get_text(strip=True).lower()
            if "hoàn" in status_text or "full" in status_text:
                story["status"] = "completed"
    
    # Description
    desc_elem = soup.select_one(".desc-text, .desc, div[itemprop='description']")
    if desc_elem:
        story["description"] = desc_elem.get_text(strip=True)
    
    # Parse chapter list
    chapters = parse_chapter_list(soup)
    story["chapters"] = chapters
    story["total_chapters"] = len(chapters)
    
    return story


def parse_chapter_list(soup: BeautifulSoup, start_index: int = 1) -> List[Dict[str, Any]]:
    """
    Parse chapter list from story page
    Filters out pagination links and only keeps real chapter links
    """
    chapters = []
    
    # Find chapter links
    chapter_links = soup.select(".list-chapter a, #list-chapter a")
    
    valid_index = start_index
    for link in chapter_links:
        try:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            
            # Skip pagination links (they don't contain 'chuong' in URL)
            if not href or "chuong" not in href.lower():
                continue
            
            # Skip if title is just a number (pagination like "1", "2", "3")
            if title.isdigit():
                continue
            
            # Skip empty or very short titles
            if len(title) < 2:
                continue
            
            # Extract chapter number from title or URL
            chapter_num = extract_chapter_number(title, href)
            
            # If we couldn't extract from title/URL, use sequential index
            if not chapter_num:
                chapter_num = valid_index
            
            chapters.append({
                "chapter_number": chapter_num,
                "title": title,
                "source_url": urljoin(BASE_URL, href),
            })
            valid_index += 1
            
        except Exception as e:
            print(f"Error parsing chapter: {e}")
            continue
    
    return chapters


def extract_chapter_number(title: str, url: str) -> Optional[int]:
    """Extract chapter number from title or URL"""
    # Try from title first: "Chương 123" or "Chapter 123"
    match = re.search(r'(?:chương|chapter)\s*(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Try from URL: /ten-truyen/chuong-123/
    match = re.search(r'chuong-(\d+)', url)
    if match:
        return int(match.group(1))
    
    return None


def parse_chapter_content(html: str, url: str) -> Dict[str, Any]:
    """
    Parse chapter content page
    Returns chapter title and content
    """
    soup = BeautifulSoup(html, "lxml")
    
    chapter = {
        "source_url": url,
        "title": "",
        "content": "",
        "chapter_number": None,
    }
    
    # Chapter title
    title_elem = soup.select_one(".chapter-title, h2 a.chapter-title, .chapter-c h2")
    if title_elem:
        chapter["title"] = title_elem.get_text(strip=True)
        chapter["chapter_number"] = extract_chapter_number(chapter["title"], url)
    
    # Chapter content
    content_elem = soup.select_one("#chapter-c, .chapter-c, .chapter-content")
    if content_elem:
        # Remove ads and unwanted elements (expanded list based on actual site)
        for unwanted in content_elem.select(".ads, script, .hidden, [style*='display:none'], .ads-responsive, .ads-mobile, .incontent-ad, div[class*='ad'], div[id*='ad']"):
            unwanted.decompose()
        
        # Get clean content - site uses <br> tags, not <p>
        # First try to get text with proper line breaks
        raw_text = content_elem.get_text(separator="\n", strip=True)
        
        # Clean up: split into lines, filter garbage, rejoin
        lines = raw_text.split("\n")
        content_parts = []
        for line in lines:
            line = line.strip()
            # Keep lines that are actual content (not too short, not ads)
            if len(line) > 5 and not any(ad in line.lower() for ad in ['quảng cáo', 'advertisement', 'ads', 'click here']):
                content_parts.append(line)
        
        chapter["content"] = "\n\n".join(content_parts)
    
    # Get next/prev chapter links
    next_elem = soup.select_one("#next_chap, a.next_chap, .btn-next")
    prev_elem = soup.select_one("#prev_chap, a.prev_chap, .btn-prev")
    
    if next_elem and next_elem.get("href"):
        chapter["next_chapter_url"] = urljoin(BASE_URL, next_elem.get("href"))
    if prev_elem and prev_elem.get("href"):
        chapter["prev_chapter_url"] = urljoin(BASE_URL, prev_elem.get("href"))
    
    return chapter


def get_pagination_info(html: str) -> Dict[str, Any]:
    """Extract pagination info from list pages"""
    soup = BeautifulSoup(html, "lxml")
    
    pagination = {
        "current_page": 1,
        "total_pages": 1,
        "next_page_url": None,
        "prev_page_url": None,
    }
    
    # Find pagination - try multiple selectors
    pager = soup.select_one(".pagination, ul.pagination, #pagination")
    if not pager:
        # Try finding in #list-chapter area
        pager = soup.select_one("#list-chapter .pagination, .list-chapter .pagination")
    
    if pager:
        # Current page
        active = pager.select_one(".active, li.active, a.active")
        if active:
            try:
                pagination["current_page"] = int(active.get_text(strip=True))
            except ValueError:
                pass
        
        # Method 1: Find "Cuối" (Last) link and extract page number
        last_link = pager.select_one("a[title*='Cuối'], a:contains('Cuối'), a:contains('»»')")
        if last_link and last_link.get("href"):
            match = re.search(r'trang-(\d+)', last_link.get("href"))
            if match:
                pagination["total_pages"] = int(match.group(1))
        
        # Method 2: Find max page from all 'trang-X' links
        if pagination["total_pages"] == 1:
            page_links = pager.select("a[href*='trang-']")
            max_page = 1
            for link in page_links:
                href = link.get("href", "")
                match = re.search(r'trang-(\d+)', href)
                if match:
                    page_num = int(match.group(1))
                    if page_num > max_page:
                        max_page = page_num
            pagination["total_pages"] = max_page
        
        # Method 3: Check for page numbers in text
        if pagination["total_pages"] == 1:
            page_items = pager.select("a, span")
            for item in page_items:
                text = item.get_text(strip=True)
                if text.isdigit():
                    page_num = int(text)
                    if page_num > pagination["total_pages"]:
                        pagination["total_pages"] = page_num
        
        # Next/Prev links
        next_link = pager.select_one("a[rel='next'], li.next a, a.next, a[title*='Sau'], a:contains('»')")
        prev_link = pager.select_one("a[rel='prev'], li.prev a, a.prev, a[title*='Trước'], a:contains('«')")
        
        if next_link and next_link.get("href"):
            pagination["next_page_url"] = urljoin(BASE_URL, next_link.get("href"))
        if prev_link and prev_link.get("href"):
            pagination["prev_page_url"] = urljoin(BASE_URL, prev_link.get("href"))
    
    print(f"[Pagination] Pages: {pagination['total_pages']}, Current: {pagination['current_page']}")
    return pagination
