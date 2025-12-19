"""
Celery Tasks
Async crawl tasks for background processing
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from .celery_app import celery_app
from app.crawler.crawler import StoryCrawler
from app.database import db


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def crawl_story_task(self, task_id: str, url: str, crawl_chapters: bool = True):
    """
    Celery task to crawl a single story
    """
    async def _crawl():
        try:
            # Update task status to running
            await db.update_task(task_id, {
                "status": "running",
                "progress": 0,
            })
            
            print(f"🕷️ Starting crawl: {url}")
            
            # Run crawler
            crawler = StoryCrawler()
            story_data = await crawler.crawl_story(url, include_chapters=crawl_chapters)
            
            # Update progress
            await db.update_task(task_id, {"progress": 50})
            
            # Save story to database
            story_record = {
                "slug": story_data["slug"],
                "title": story_data["title"],
                "author": story_data.get("author"),
                "description": story_data.get("description"),
                "genres": story_data.get("genres", []),
                "status": story_data.get("status", "ongoing"),
                "total_chapters": story_data.get("total_chapters", 0),
                "cover_url": story_data.get("cover_url"),
                "source_url": story_data.get("source_url"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            saved_story = await db.upsert_story(story_record)
            story_id = saved_story.get("id") if saved_story else None
            
            # Save chapters
            if story_id and crawl_chapters and story_data.get("chapters"):
                chapters_to_save = []
                for ch in story_data["chapters"]:
                    if ch.get("content"):
                        chapters_to_save.append({
                            "story_id": story_id,
                            "chapter_number": ch["chapter_number"],
                            "title": ch.get("title", f"Chương {ch['chapter_number']}"),
                            "content": ch["content"],
                            "source_url": ch.get("source_url", ""),
                        })
                
                if chapters_to_save:
                    await db.bulk_upsert_chapters(chapters_to_save)
            
            # Update progress
            await db.update_task(task_id, {"progress": 90})
            
            # Mark as completed
            await db.update_task(task_id, {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            
            print(f"✅ Crawl completed: {story_data['title']}")
            return {"status": "success", "story_slug": story_data["slug"]}
            
        except Exception as e:
            print(f"❌ Crawl failed: {e}")
            await db.update_task(task_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            raise
    
    try:
        return run_async(_crawl())
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2)
def crawl_story_list_task(self, category: str = "hot", max_pages: int = 2):
    """
    Celery task to crawl story listing pages
    """
    async def _crawl_list():
        print(f"📃 Crawling {category} stories, {max_pages} pages...")
        
        crawler = StoryCrawler()
        stories = []
        
        if category == "hot":
            stories = await crawler.crawl_hot_stories(max_pages)
        elif category == "new":
            stories = await crawler.crawl_new_stories(max_pages)
        elif category == "completed":
            stories = await crawler.crawl_completed_stories(max_pages)
        
        # Save basic story info
        for story in stories:
            story_record = {
                "slug": story["slug"],
                "title": story["title"],
                "author": story.get("author"),
                "source_url": story.get("source_url"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.upsert_story(story_record)
        
        print(f"✅ Found {len(stories)} stories")
        return {"status": "success", "count": len(stories)}
    
    return run_async(_crawl_list())


@celery_app.task
def check_story_updates():
    """
    Scheduled task to check for story updates
    Runs every 30 minutes via Celery Beat
    """
    async def _check_updates():
        print("🔄 Checking for story updates...")
        
        # Get all ongoing stories
        stories = await db.get_stories(limit=50)
        ongoing = [s for s in stories if s.get("status") == "ongoing"]
        
        print(f"📚 Found {len(ongoing)} ongoing stories to check")
        
        # For each story, queue a lightweight check
        for story in ongoing:
            if story.get("source_url"):
                # Queue a crawl task for each (with rate limiting)
                crawl_story_task.apply_async(
                    args=[None, story["source_url"], False],  # Don't crawl chapters
                    countdown=60  # Stagger requests
                )
        
        return {"status": "success", "checked": len(ongoing)}
    
    return run_async(_check_updates())


@celery_app.task
def test_celery():
    """Simple test task"""
    print("🧪 Celery is working!")
    return {"status": "ok", "message": "Celery is configured correctly"}
