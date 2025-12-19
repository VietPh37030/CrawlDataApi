"""
Scheduler - Auto crawl mỗi 15 phút
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

class CrawlScheduler:
    def __init__(self):
        self.is_running = False
        self.auto_enabled = False
        self.interval_minutes = 15
        self.last_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        
    async def start_auto_crawl(self):
        """Bật auto-crawl"""
        if self.auto_enabled:
            return {"status": "already_running"}
        
        self.auto_enabled = True
        self.task = asyncio.create_task(self._auto_crawl_loop())
        print(f"🔄 Auto-crawl ENABLED - Every {self.interval_minutes} minutes")
        return {"status": "started", "interval": self.interval_minutes}
    
    def stop_auto_crawl(self):
        """Tắt auto-crawl VÀ dừng manual crawl"""
        self.auto_enabled = False
        self.is_running = False  # Dừng manual crawl
        if self.task:
            self.task.cancel()
            self.task = None
        print("⏹️ Crawler STOPPED")
        return {"status": "stopped"}
    
    async def _auto_crawl_loop(self):
        """Loop chạy auto crawl"""
        while self.auto_enabled:
            try:
                print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Auto-crawl triggered!")
                await self._run_crawl_job()
                self.last_run = datetime.now()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Auto-crawl error: {e}")
                await asyncio.sleep(60)
    
    async def _run_crawl_job(self):
        """Chạy crawl job"""
        from .crawler.crawler import StoryCrawler
        from .database import Database
        
        crawler = StoryCrawler()
        db = Database()
        
        print("📚 Crawling new stories...")
        try:
            stories = await crawler.crawl_story_list(
                f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
                max_pages=2
            )
            
            for story_info in stories[:10]:
                if not self.auto_enabled:
                    break
                    
                try:
                    await self._crawl_and_save_story(crawler, db, story_info["source_url"])
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    continue
                    
            print(f"✅ Auto-crawl completed!")
        except Exception as e:
            print(f"❌ Crawl job failed: {e}")
    
    async def _crawl_and_save_story(self, crawler, db, url: str):
        """Crawl và lưu 1 truyện + chapters"""
        story = await crawler.crawl_story(url, include_chapters=False)
        
        # Lưu story
        story_record = {
            "slug": story["slug"],
            "title": story["title"],
            "author": story.get("author"),
            "description": story.get("description"),
            "genres": story.get("genres", []),
            "status": "Full" if story.get("status") == "completed" else "Đang ra",
            "total_chapters": story.get("total_chapters", 0),
            "cover_url": story.get("cover_url"),
            "source_url": story.get("source_url"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        saved_story = await db.upsert_story(story_record)
        story_id = saved_story.get("id") if saved_story else None
        
        if not story_id:
            existing = await db.get_story_by_slug(story["slug"])
            story_id = existing["id"] if existing else None
        
        if not story_id:
            print(f"  ❌ Cannot save: {story['title']}")
            return
        
        # Lưu chapters (metadata, không cần content)
        chapters = story.get("chapters", [])
        saved_count = 0
        
        for ch in chapters:
            try:
                chapter_record = {
                    "story_id": story_id,
                    "chapter_number": ch.get("chapter_number", 0),
                    "title": ch.get("title", ""),
                    "source_url": ch.get("source_url", ""),
                    "content": "",  # Không crawl content để tiết kiệm thời gian
                }
                await db.upsert_chapter(chapter_record)
                saved_count += 1
            except Exception:
                continue
        
        print(f"  ✅ {story['title']} ({saved_count} chapters saved)")
    
    async def manual_crawl(self, categories: list, max_pages: int):
        """Crawl thủ công - chạy liên tục cho đến khi xong hoặc bị dừng"""
        if self.is_running:
            return {"status": "busy", "message": "Crawler đang chạy"}
        
        self.is_running = True
        print(f"🚀 Manual crawl started: {categories}, {max_pages} pages each")
        
        try:
            from .crawler.crawler import StoryCrawler
            from .database import Database
            
            crawler = StoryCrawler()
            db = Database()
            
            category_urls = {
                "hot": f"{crawler.settings.base_url}/danh-sach/truyen-hot/",
                "new": f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
                "completed": f"{crawler.settings.base_url}/danh-sach/truyen-full/",
            }
            
            total_crawled = 0
            
            for category in categories:
                if not self.is_running:
                    print("⏹️ Crawl stopped by user")
                    break
                    
                if category not in category_urls:
                    continue
                    
                print(f"\n📖 Crawling category: {category}")
                stories = await crawler.crawl_story_list(category_urls[category], max_pages=max_pages)
                
                for story_info in stories:
                    if not self.is_running:
                        print("⏹️ Crawl stopped by user")
                        break
                        
                    try:
                        await self._crawl_and_save_story(crawler, db, story_info["source_url"])
                        total_crawled += 1
                    except Exception as e:
                        print(f"  ❌ Error: {e}")
                        continue
            
            print(f"\n🎉 Manual crawl completed! Total: {total_crawled} stories")
            return {"status": "completed", "total": total_crawled}
            
        except Exception as e:
            print(f"❌ Manual crawl failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            self.is_running = False
    
    def get_status(self):
        """Lấy trạng thái scheduler"""
        return {
            "auto_enabled": self.auto_enabled,
            "is_crawling": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }

# Singleton instance
scheduler = CrawlScheduler()
