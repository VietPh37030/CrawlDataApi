"""
Bulk Crawler Runner - Crawl nhiều truyện từ listing pages
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Setup path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.database import Database
from app.crawler.crawler import StoryCrawler

async def bulk_crawl_stories(bulk_task_id: str, categories: list, max_pages: int, crawl_chapters: bool):
    """
    Crawl toàn bộ truyện từ các trang danh sách
    """
    print(f"🚀 Bulk Crawler: Starting task {bulk_task_id}")
    print(f"📚 Categories: {categories}, Max pages: {max_pages}")
    
    db = Database()
    crawler = StoryCrawler()
    
    # Map categories to URLs
    category_urls = {
        "hot": f"{crawler.settings.base_url}/danh-sach/truyen-hot/",
        "new": f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
        "completed": f"{crawler.settings.base_url}/danh-sach/truyen-full/",
    }
    
    all_stories_urls = []
    
    try:
        # Bước 1: Lấy danh sách URLs của tất cả truyện
        for category in categories:
            if category not in category_urls:
                print(f"⚠️ Unknown category: {category}")
                continue
            
            print(f"\n📖 Crawling category: {category}")
            list_url = category_urls[category]
            
            stories = await crawler.crawl_story_list(list_url, max_pages=max_pages)
            print(f"✅ Found {len(stories)} stories in {category}")
            
            # Lấy URL của từng truyện
            for story in stories:
                if story.get("source_url"):
                    all_stories_urls.append(story["source_url"])
        
        # Loại bỏ trùng lặp
        all_stories_urls = list(set(all_stories_urls))
        print(f"\n🎯 Total unique stories: {len(all_stories_urls)}")
        
        # Bước 2: Crawl từng truyện
        for i, story_url in enumerate(all_stories_urls):
            try:
                print(f"\n[{i+1}/{len(all_stories_urls)}] Crawling: {story_url}")
                
                # Crawl story info
                story_data = await crawler.crawl_story(story_url, include_chapters=False)
                
                # Save story to DB
                story_record = {
                    "slug": story_data["slug"],
                    "title": story_data["title"],
                    "author": story_data.get("author"),
                    "description": story_data.get("description"),
                    "genres": story_data.get("genres", []),
                    "status": "Full" if story_data.get("status") == "completed" else "Đang ra",
                    "total_chapters": story_data.get("total_chapters", 0),
                    "cover_url": story_data.get("cover_url"),
                    "source_url": story_data.get("source_url"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                
                saved_story = await db.upsert_story(story_record)
                story_id = saved_story.get("id") if saved_story else None
                
                if not story_id:
                    existing = await db.get_story_by_slug(story_data["slug"])
                    story_id = existing["id"] if existing else None
                
                if not story_id:
                    print(f"❌ Failed to save story: {story_data['title']}")
                    continue
                
                print(f"✅ Saved story: {story_data['title']} ({story_data.get('total_chapters', 0)} chapters)")
                
                # Crawl chapters nếu được yêu cầu
                if crawl_chapters and story_data.get("chapters"):
                    total_chapters = len(story_data["chapters"])
                    print(f"📄 Crawling {total_chapters} chapters...")
                    
                    for j, chapter_info in enumerate(story_data["chapters"]):
                        try:
                            # Update mỗi 10 chương
                            if j % 10 == 0:
                                print(f"  [{j+1}/{total_chapters}] Crawling chapters...")
                            
                            chapter_data = await crawler.crawl_single_chapter(chapter_info["source_url"])
                            
                            if chapter_data and chapter_data.get("content"):
                                chapter_record = {
                                    "story_id": story_id,
                                    "chapter_number": chapter_info.get("chapter_number", j + 1),
                                    "title": chapter_data.get("title") or chapter_info.get("title"),
                                    "content": chapter_data.get("content", ""),
                                    "source_url": chapter_info["source_url"],
                                }
                                await db.upsert_chapter(chapter_record)
                        except Exception as e:
                            print(f"  ❌ Error chapter {j+1}: {e}")
                            continue
                    
                    print(f"✅ Finished crawling chapters for: {story_data['title']}")
                
            except Exception as e:
                print(f"❌ Error crawling {story_url}: {e}")
                continue
        
        print(f"\n🎉 Bulk crawl completed! Total stories processed: {len(all_stories_urls)}")
        
    except Exception as e:
        print(f"❌ Bulk crawler failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python -m app.crawler.bulk_runner <bulk_task_id> <categories> <max_pages> [crawl_chapters]")
        sys.exit(1)
    
    bulk_task_id = sys.argv[1]
    categories = sys.argv[2].split(",")
    max_pages = int(sys.argv[3])
    crawl_chapters = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False
    
    asyncio.run(bulk_crawl_stories(bulk_task_id, categories, max_pages, crawl_chapters))
