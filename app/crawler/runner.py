import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
# Ensure we can import 'app' module
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Set Windows Event Loop Policy for Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.database import Database
from app.crawler.crawler import StoryCrawler

async def run_full_crawl(task_id: str, url: str, crawl_chapters: bool):
    """
    Standalone crawler process
    """
    print(f"🚀 Runner: Starting task {task_id}")
    db = Database()
    
    try:
        await db.update_task(task_id, {
            "status": "processing",
            "message": "Đang tải thông tin truyện (Runner)...",
            "progress": 5,
        })
        
        crawler = StoryCrawler()
        
        # Crawl story info
        print(f"📖 Crawling story info: {url}")
        story_data = await crawler.crawl_story(url, include_chapters=False)
        
        await db.update_task(task_id, {
            "message": f"Đang lưu thông tin: {story_data.get('title')}",
            "progress": 10,
        })
        
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
            # Fallback retrieve if upsert return None (sometimes happens on update)
            existing = await db.get_story_by_slug(story_data["slug"])
            story_id = existing["id"] if existing else None
            
        if not story_id:
            raise Exception("Không thể lưu truyện vào database")
        
        # Crawl chapters
        if crawl_chapters and story_data.get("chapters"):
            total_chapters = len(story_data["chapters"])
            print(f"📚 Found {total_chapters} chapters to crawl")
            
            for i, chapter_info in enumerate(story_data["chapters"]):
                try:
                    progress = 10 + int((i / total_chapters) * 85)
                    
                    # Update status every 5 chapters to reduce db load
                    if i % 3 == 0:
                        await db.update_task(task_id, {
                            "message": f"Đang tải chương {i+1}/{total_chapters}...",
                            "progress": progress,
                        })
                    
                    # Crawl chapter content
                    chapter_data = await crawler.crawl_single_chapter(chapter_info["source_url"])
                    
                    if chapter_data and chapter_data.get("content"):
                        chapter_record = {
                            "story_id": story_id,
                            "chapter_number": chapter_info.get("chapter_number", i + 1),
                            "title": chapter_data.get("title") or chapter_info.get("title"),
                            "content": chapter_data.get("content", ""),
                            "source_url": chapter_info["source_url"],
                        }
                        await db.upsert_chapter(chapter_record)
                    else:
                        print(f"⚠️ Failed to get content for chapter {i+1}")
                        
                except Exception as e:
                    print(f"❌ Error crawling chapter {i+1}: {e}")
                    # Continue to next chapter
                    continue
        
        # Mark as completed
        await db.update_task(task_id, {
            "status": "completed",
            "message": "Hoàn thành cào dữ liệu!",
            "progress": 100,
            "novel_id": story_id,
            "total_chapters": story_data.get("total_chapters", 0),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        print("✅ Runner: Task completed successfully")
        
    except Exception as e:
        print(f"❌ Runner failed: {e}")
        await db.update_task(task_id, {
            "status": "failed",
            "error": str(e),
            "message": f"Lỗi runner: {str(e)}",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m app.crawler.runner <task_id> <url> [crawl_chapters]")
        sys.exit(1)
        
    task_id = sys.argv[1]
    url = sys.argv[2]
    # "True" or "true" -> True
    crawl_chapters = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    asyncio.run(run_full_crawl(task_id, url, crawl_chapters))
