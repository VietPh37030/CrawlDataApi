"""
Scheduler - Auto crawl mỗi 15 phút
"""
import asyncio
from datetime import datetime
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
        """Tắt auto-crawl"""
        self.auto_enabled = False
        if self.task:
            self.task.cancel()
            self.task = None
        print("⏹️ Auto-crawl DISABLED")
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
                await asyncio.sleep(60)  # Wait 1 min before retry
    
    async def _run_crawl_job(self):
        """Chạy crawl job"""
        from .crawler.crawler import StoryCrawler
        from .database import Database
        from datetime import timezone
        
        crawler = StoryCrawler()
        db = Database()
        
        # Crawl 2 trang truyện mới
        print("📚 Crawling new stories...")
        try:
            stories = await crawler.crawl_story_list(
                f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
                max_pages=2
            )
            
            for story_info in stories[:10]:  # Giới hạn 10 truyện mỗi lần
                try:
                    story = await crawler.crawl_story(story_info["source_url"], include_chapters=False)
                    
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
                    
                    await db.upsert_story(story_record)
                    print(f"  ✅ {story['title']} - {story.get('total_chapters', 0)} chapters")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    continue
                    
            print(f"✅ Auto-crawl completed! {len(stories)} stories checked")
        except Exception as e:
            print(f"❌ Crawl job failed: {e}")
    
    async def manual_crawl(self, categories: list, max_pages: int):
        """Crawl thủ công - chạy liên tục cho đến khi xong"""
        if self.is_running:
            return {"status": "busy", "message": "Crawler đang chạy"}
        
        self.is_running = True
        print(f"🚀 Manual crawl started: {categories}, {max_pages} pages each")
        
        try:
            from .crawler.crawler import StoryCrawler
            from .database import Database
            from datetime import timezone
            
            crawler = StoryCrawler()
            db = Database()
            
            category_urls = {
                "hot": f"{crawler.settings.base_url}/danh-sach/truyen-hot/",
                "new": f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
                "completed": f"{crawler.settings.base_url}/danh-sach/truyen-full/",
            }
            
            total_crawled = 0
            
            for category in categories:
                if category not in category_urls:
                    continue
                    
                print(f"\n📖 Crawling category: {category}")
                stories = await crawler.crawl_story_list(category_urls[category], max_pages=max_pages)
                
                for story_info in stories:
                    try:
                        story = await crawler.crawl_story(story_info["source_url"], include_chapters=False)
                        
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
                        
                        await db.upsert_story(story_record)
                        total_crawled += 1
                        print(f"  ✅ [{total_crawled}] {story['title']}")
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
