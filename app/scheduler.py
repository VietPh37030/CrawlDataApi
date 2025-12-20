"""
Scheduler - Auto crawl mỗi 15 phút + Realtime Log
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from collections import deque

class CrawlScheduler:
    def __init__(self):
        self.is_running = False
        self.auto_enabled = False
        self.interval_minutes = 15
        self.last_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        
        # Realtime tracking
        self.current_story = ""
        self.current_story_title = ""
        self.crawl_logs: deque = deque(maxlen=20)  # Last 20 logs
        self.stats = {
            "stories_crawled": 0,
            "chapters_saved": 0,
            "errors": 0,
        }
        
        # Progress tracking for current story
        self.progress = {
            "current_chapter": 0,
            "total_chapters": 0,
            "percent": 0,
            "status": "idle",  # idle, crawling_list, crawling_story, saving_chapters, done
        }
        
    def _log(self, message: str):
        """Add log entry"""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": message
        }
        self.crawl_logs.append(entry)
        print(f"[{entry['time']}] {message}")
        
    async def start_auto_crawl(self):
        """Bật auto-crawl"""
        if self.auto_enabled:
            return {"status": "already_running"}
        
        self.auto_enabled = True
        self.task = asyncio.create_task(self._auto_crawl_loop())
        self._log("🔄 Auto-crawl đã BẬT")
        return {"status": "started", "interval": self.interval_minutes}
    
    def stop_auto_crawl(self):
        """Tắt auto-crawl VÀ dừng manual crawl"""
        self.auto_enabled = False
        self.is_running = False
        if self.task:
            self.task.cancel()
            self.task = None
        self.current_story = ""
        self._log("⏹️ Crawler đã DỪNG")
        return {"status": "stopped"}
    
    async def _auto_crawl_loop(self):
        """Loop chạy auto crawl"""
        while self.auto_enabled:
            try:
                self._log("⏰ Auto-crawl bắt đầu!")
                await self._run_crawl_job()
                self.last_run = datetime.now()
                self._log(f"✅ Auto-crawl xong! Đợi {self.interval_minutes} phút...")
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"❌ Lỗi: {e}")
                await asyncio.sleep(60)
    
    async def _run_crawl_job(self):
        """Chạy crawl job"""
        from .crawler.crawler import StoryCrawler
        from .database import Database
        
        crawler = StoryCrawler()
        db = Database()
        
        self._log("📚 Đang lấy danh sách truyện mới...")
        try:
            stories = await crawler.crawl_story_list(
                f"{crawler.settings.base_url}/danh-sach/truyen-moi/",
                max_pages=2
            )
            self._log(f"📋 Tìm thấy {len(stories)} truyện")
            
            for story_info in stories[:10]:
                if not self.auto_enabled:
                    break
                try:
                    await self._crawl_and_save_story(crawler, db, story_info["source_url"])
                except Exception as e:
                    self.stats["errors"] += 1
                    continue
                    
        except Exception as e:
            self._log(f"❌ Lỗi crawl: {e}")
    
    async def _crawl_and_save_story(self, crawler, db, url: str):
        """Crawl và lưu 1 truyện + TẤT CẢ chapters trước khi sang truyện khác"""
        # Extract title from URL for display
        slug = url.rstrip('/').split('/')[-1]
        self.current_story = slug
        self.progress["status"] = "crawling_story"
        self.progress["current_chapter"] = 0
        self.progress["total_chapters"] = 0
        self.progress["percent"] = 0
        self._log(f"📖 Bắt đầu crawl: {slug}")
        
        try:
            # Crawl story VÀ lấy danh sách chapters từ TẤT CẢ pages
            # include_chapters=False nghĩa là không crawl NỘI DUNG chapter (chậm)
            # nhưng VẪN lấy DANH SÁCH chapters (title, source_url, chapter_number)
            story = await crawler.crawl_story(url, include_chapters=False)
            
            raw_chapters = story.get("chapters", [])
            
            # Khử trùng lặp chapter_number trước khi lưu
            # Vì Postgres không cho phép có 2 dòng cùng unique key trong 1 lệnh UPSERT batch
            seen_chapters = {}
            for ch in raw_chapters:
                ch_num = ch.get("chapter_number")
                if ch_num not in seen_chapters:
                    seen_chapters[ch_num] = ch
            
            chapters = list(seen_chapters.values())
            # Sắp xếp lại theo số chương
            chapters.sort(key=lambda x: x.get("chapter_number", 0))
            
            total_chapters = len(chapters)
            self.progress["total_chapters"] = total_chapters
            self._log(f"  📋 Tìm thấy {len(raw_chapters)} chương (Khử trùng còn {total_chapters})")
            
            if total_chapters == 0:
                self._log(f"  ⚠️ Không tìm thấy chapter nào, bỏ qua")
                return
            
            # Lưu story trước
            story_record = {
                "slug": story["slug"],
                "title": story["title"],
                "author": story.get("author"),
                "description": story.get("description"),
                "genres": story.get("genres", []),
                "status": "Full" if story.get("status") == "completed" else "Đang ra",
                "total_chapters": total_chapters,
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
                self._log(f"  ❌ Không lưu được truyện: {story['title']}")
                self.stats["errors"] += 1
                return
            
            self.current_story_title = story['title']
            self.progress["status"] = "saving_chapters"
            self._log(f"  ✅ Đã lưu truyện: {story['title'][:40]}")
            
            # Lưu TẤT CẢ chapters theo batch để tối ưu
            saved_count = 0
            batch_size = 50
            
            for i in range(0, total_chapters, batch_size):
                if not self.is_running and not self.auto_enabled:
                    self._log(f"  ⏹️ Đã dừng giữa chừng")
                    break
                    
                batch = chapters[i:i + batch_size]
                chapter_records = []
                
                for ch in batch:
                    chapter_records.append({
                        "story_id": story_id,
                        "chapter_number": ch.get("chapter_number", 0),
                        "title": ch.get("title", ""),
                        "source_url": ch.get("source_url", ""),
                        "content": "",  # Content sẽ crawl sau nếu cần
                    })
                
                try:
                    await db.bulk_upsert_chapters(chapter_records)
                    saved_count += len(chapter_records)
                    
                    # Log tiến trình + cập nhật progress
                    progress = min(i + batch_size, total_chapters)
                    self.progress["current_chapter"] = progress
                    self.progress["percent"] = int((progress / total_chapters) * 100) if total_chapters > 0 else 0
                    self._log(f"  📝 Đã lưu {progress}/{total_chapters} chapters ({self.progress['percent']}%)")
                except Exception as e:
                    self._log(f"  ⚠️ Lỗi batch {i}: {e}")
                    # Fallback: lưu từng chapter
                    for ch_rec in chapter_records:
                        try:
                            await db.upsert_chapter(ch_rec)
                            saved_count += 1
                        except Exception:
                            continue
            
            self.stats["stories_crawled"] += 1
            self.stats["chapters_saved"] += saved_count
            self.progress["status"] = "done"
            self.progress["percent"] = 100
            self._log(f"  🎉 Hoàn thành: {story['title'][:30]}... ({saved_count}/{total_chapters} chương)")
            
            # Cập nhật thống kê vào database để charts hiển thị
            try:
                await db.update_crawl_stats(stories=1, chapters=saved_count)
            except Exception as stats_error:
                self._log(f"  ⚠️ Lỗi cập nhật stats: {stats_error}")
            
        except Exception as e:
            self._log(f"  ❌ Lỗi crawl {slug}: {e}")
            self.stats["errors"] += 1
    
    async def manual_crawl(self, categories: list, max_pages: int):
        """Crawl thủ công"""
        if self.is_running:
            return {"status": "busy", "message": "Crawler đang chạy"}
        
        self.is_running = True
        self.stats = {"stories_crawled": 0, "chapters_saved": 0, "errors": 0}
        self._log(f"🚀 Bắt đầu crawl: {categories}")
        
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
            
            for category in categories:
                if not self.is_running:
                    self._log("⏹️ Đã dừng bởi người dùng")
                    break
                    
                if category not in category_urls:
                    continue
                    
                self._log(f"📂 Danh mục: {category}")
                stories = await crawler.crawl_story_list(category_urls[category], max_pages=max_pages)
                self._log(f"  📋 Tìm thấy {len(stories)} truyện")
                
                for story_info in stories:
                    if not self.is_running:
                        break
                    try:
                        await self._crawl_and_save_story(crawler, db, story_info["source_url"])
                    except Exception as e:
                        self.stats["errors"] += 1
                        continue
            
            self._log(f"🎉 Hoàn thành! {self.stats['stories_crawled']} truyện, {self.stats['chapters_saved']} chương")
            return {"status": "completed", "stats": self.stats}
            
        except Exception as e:
            self._log(f"❌ Lỗi: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            self.is_running = False
            self.current_story = ""
    
    def get_status(self):
        """Lấy trạng thái scheduler"""
        return {
            "auto_enabled": self.auto_enabled,
            "is_crawling": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "current_story": self.current_story,
            "current_story_title": self.current_story_title,
            "progress": self.progress,
            "stats": self.stats,
            "logs": list(self.crawl_logs),
        }

# Singleton instance
scheduler = CrawlScheduler()
