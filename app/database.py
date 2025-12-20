"""
Supabase Database Connection - Full CRUD Operations
"""
from supabase import create_client, Client
from functools import lru_cache
from .config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance"""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


class Database:
    """Database operations wrapper for Supabase"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # ========== Stories (Novels) ==========
    
    async def create_story(self, story_data: dict) -> dict:
        """Insert a new story"""
        result = self.client.table("stories").insert(story_data).execute()
        return result.data[0] if result.data else None
    
    async def get_story_by_slug(self, slug: str) -> dict | None:
        """Get story by slug"""
        result = self.client.table("stories").select("*").eq("slug", slug).execute()
        return result.data[0] if result.data else None
    
    async def get_story_by_id(self, story_id: str) -> dict | None:
        """Get story by UUID"""
        result = self.client.table("stories").select("*").eq("id", story_id).execute()
        return result.data[0] if result.data else None
    
    async def get_stories(self, limit: int = 50, offset: int = 0) -> list:
        """Get paginated stories"""
        result = self.client.table("stories").select("*").range(offset, offset + limit - 1).order("updated_at", desc=True).execute()
        return result.data or []
    
    async def update_story(self, story_id: str, story_data: dict) -> dict:
        """Update story by ID"""
        result = self.client.table("stories").update(story_data).eq("id", story_id).execute()
        return result.data[0] if result.data else None
    
    async def upsert_story(self, story_data: dict) -> dict:
        """Insert or update story by slug"""
        result = self.client.table("stories").upsert(story_data, on_conflict="slug").execute()
        return result.data[0] if result.data else None
    
    async def search_stories(self, query: str, limit: int = 20) -> list:
        """Search stories by title or author"""
        result = self.client.table("stories").select("*").or_(
            f"title.ilike.%{query}%,author.ilike.%{query}%"
        ).limit(limit).execute()
        return result.data or []
    
    async def get_stories_count(self) -> int:
        """Get total count of stories"""
        result = self.client.table("stories").select("id", count="exact").execute()
        return result.count or 0
    
    # ========== Chapters ==========
    
    async def create_chapter(self, chapter_data: dict) -> dict:
        """Insert a new chapter"""
        result = self.client.table("chapters").insert(chapter_data).execute()
        return result.data[0] if result.data else None
    
    async def get_chapter_by_id(self, chapter_id: str) -> dict | None:
        """Get chapter by UUID"""
        result = self.client.table("chapters").select("*").eq("id", chapter_id).execute()
        return result.data[0] if result.data else None
    
    async def get_chapters_by_story(self, story_id: str, limit: int = 100, offset: int = 0) -> list:
        """Get chapters for a story with pagination"""
        result = self.client.table("chapters").select("*").eq("story_id", story_id).range(offset, offset + limit - 1).order("chapter_number").execute()
        return result.data or []
    
    async def get_chapter(self, story_id: str, chapter_number: int) -> dict | None:
        """Get specific chapter by story_id and chapter_number"""
        result = self.client.table("chapters").select("*").eq("story_id", story_id).eq("chapter_number", chapter_number).execute()
        return result.data[0] if result.data else None
    
    async def upsert_chapter(self, chapter_data: dict) -> dict:
        """Insert or update chapter"""
        result = self.client.table("chapters").upsert(
            chapter_data, 
            on_conflict="story_id,chapter_number"
        ).execute()
        return result.data[0] if result.data else None
    
    async def bulk_upsert_chapters(self, chapters: list) -> list:
        """Bulk insert/update chapters with logging"""
        if not chapters:
            return []
        
        try:
            result = self.client.table("chapters").upsert(
                chapters,
                on_conflict="story_id,chapter_number"
            ).execute()
            
            saved_count = len(result.data) if result.data else 0
            print(f"[DB] Upserted {saved_count}/{len(chapters)} chapters")
            return result.data or []
        except Exception as e:
            print(f"[DB ERROR] bulk_upsert_chapters failed: {e}")
            # Try one by one as fallback
            saved = []
            for ch in chapters:
                try:
                    r = self.client.table("chapters").upsert(
                        ch, on_conflict="story_id,chapter_number"
                    ).execute()
                    if r.data:
                        saved.extend(r.data)
                except Exception as inner_e:
                    print(f"[DB ERROR] Single chapter upsert failed: {inner_e}")
            print(f"[DB] Fallback saved {len(saved)}/{len(chapters)} chapters")
            return saved
    
    async def get_chapters_count(self, story_id: str) -> int:
        """Get total count of chapters for a story"""
        result = self.client.table("chapters").select("id", count="exact").eq("story_id", story_id).execute()
        return result.count or 0
    
    # ========== Crawl Tasks ==========
    
    async def create_task(self, task_data: dict) -> dict:
        """Create a new crawl task"""
        result = self.client.table("crawl_tasks").insert(task_data).execute()
        return result.data[0] if result.data else None
    
    async def get_task(self, task_id: str) -> dict | None:
        """Get task by ID"""
        result = self.client.table("crawl_tasks").select("*").eq("id", task_id).execute()
        return result.data[0] if result.data else None
    
    async def update_task(self, task_id: str, task_data: dict) -> dict:
        """Update task status"""
        result = self.client.table("crawl_tasks").update(task_data).eq("id", task_id).execute()
        return result.data[0] if result.data else None
    
    # ========== Genres ==========
    
    async def get_or_create_genre(self, name: str, slug: str) -> dict:
        """Get genre by name or create if not exists"""
        result = self.client.table("genres").select("*").eq("slug", slug).execute()
        if result.data:
            return result.data[0]
        # Create new
        new_genre = {"name": name, "slug": slug}
        result = self.client.table("genres").insert(new_genre).execute()
        return result.data[0] if result.data else None
    
    async def link_story_genre(self, story_id: str, genre_id: str):
        """Link story to genre"""
        try:
            self.client.table("story_genres").upsert({
                "story_id": story_id, 
                "genre_id": genre_id
            }).execute()
        except Exception:
            pass  # Ignore duplicate
    
    async def get_genres(self) -> list:
        """Get all genres with story count"""
        result = self.client.table("genres").select("*").order("story_count", desc=True).execute()
        return result.data or []
    
    # ========== Crawl Stats ==========
    
    async def update_crawl_stats(self, stories: int = 0, chapters: int = 0, content: int = 0, errors: int = 0):
        """Update today's crawl statistics"""
        from datetime import date
        today = date.today().isoformat()
        
        # Try to get existing record
        result = self.client.table("crawl_stats").select("*").eq("date", today).execute()
        
        if result.data:
            # Update existing
            existing = result.data[0]
            self.client.table("crawl_stats").update({
                "stories_crawled": existing["stories_crawled"] + stories,
                "chapters_crawled": existing["chapters_crawled"] + chapters,
                "content_fetched": existing["content_fetched"] + content,
                "errors": existing["errors"] + errors,
            }).eq("date", today).execute()
        else:
            # Create new
            self.client.table("crawl_stats").insert({
                "date": today,
                "stories_crawled": stories,
                "chapters_crawled": chapters,
                "content_fetched": content,
                "errors": errors,
            }).execute()
    
    async def get_crawl_stats(self, days: int = 7) -> list:
        """Get crawl stats for last N days"""
        result = self.client.table("crawl_stats").select("*").order("date", desc=True).limit(days).execute()
        return result.data or []
    
    # ========== Reading History ==========
    
    async def add_reading_history(self, user_id: str, story_id: str, chapter_id: str):
        """Add reading history entry"""
        self.client.table("reading_history").insert({
            "user_id": user_id,
            "story_id": story_id,
            "chapter_id": chapter_id,
        }).execute()
    
    async def get_reading_history(self, user_id: str, limit: int = 20) -> list:
        """Get user's reading history"""
        result = self.client.table("reading_history").select(
            "*, stories(id, title, cover_url), chapters(id, chapter_number, title)"
        ).eq("user_id", user_id).order("read_at", desc=True).limit(limit).execute()
        return result.data or []
    
    # ========== Storage (GZIP Compressed Chapter Content) ==========
    
    STORAGE_BUCKET = "chapters"
    
    def _get_storage_path(self, story_id: str, chapter_number: int) -> str:
        """Generate storage path for chapter content"""
        return f"{story_id}/chap_{chapter_number}.gz"
    
    async def upload_chapter_content(self, story_id: str, chapter_number: int, content: str) -> bool:
        """
        Compress and upload chapter content to Supabase Storage
        Returns True if successful
        """
        import gzip
        
        if not content:
            return False
        
        try:
            # Compress content with GZIP
            compressed_data = gzip.compress(content.encode('utf-8'))
            path = self._get_storage_path(story_id, chapter_number)
            
            # Upload to storage
            result = self.client.storage.from_(self.STORAGE_BUCKET).upload(
                path,
                compressed_data,
                file_options={"content-type": "application/octet-stream", "upsert": "true"}
            )
            
            print(f"[Storage] Uploaded {path} ({len(content)} chars -> {len(compressed_data)} bytes)")
            
            # Update chapter record with storage path
            self.client.table("chapters").update({
                "storage_path": path,
                "is_archived": True,
                "content": None  # Clear DB content to save space
            }).eq("story_id", story_id).eq("chapter_number", chapter_number).execute()
            
            return True
        except Exception as e:
            print(f"[Storage ERROR] Upload failed: {e}")
            return False
    
    async def download_chapter_content(self, story_id: str, chapter_number: int) -> str | None:
        """
        Download and decompress chapter content from Supabase Storage
        Returns content string or None if not found
        """
        import gzip
        
        try:
            path = self._get_storage_path(story_id, chapter_number)
            
            # Download from storage
            data = self.client.storage.from_(self.STORAGE_BUCKET).download(path)
            
            if data:
                # Decompress
                content = gzip.decompress(data).decode('utf-8')
                print(f"[Storage] Downloaded {path} ({len(data)} bytes -> {len(content)} chars)")
                return content
            return None
        except Exception as e:
            print(f"[Storage] Download failed for {story_id}/chap_{chapter_number}: {e}")
            return None
    
    async def get_chapter_content(self, story_id: str, chapter_number: int) -> str | None:
        """
        Get chapter content - tries Storage first, then DB column
        """
        # Try storage first
        content = await self.download_chapter_content(story_id, chapter_number)
        if content:
            return content
        
        # Fallback to DB column (legacy)
        chapter = await self.get_chapter(story_id, chapter_number)
        if chapter and chapter.get("content"):
            return chapter["content"]
        
        return None
    
    async def is_chapter_archived(self, story_id: str, chapter_number: int) -> bool:
        """Check if chapter content is saved in storage"""
        chapter = await self.get_chapter(story_id, chapter_number)
        return chapter.get("is_archived", False) if chapter else False
    
    async def clear_all_data(self) -> dict:
        """
        XÓA TOÀN BỘ DATA - Stories, Chapters, và Storage
        Dùng để re-crawl từ đầu
        """
        try:
            # 1. Delete all chapters first (foreign key constraint)
            chapters_result = self.client.table("chapters").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            chapters_deleted = len(chapters_result.data) if chapters_result.data else 0
            
            # 2. Delete all stories
            stories_result = self.client.table("stories").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            stories_deleted = len(stories_result.data) if stories_result.data else 0
            
            # 3. Clear storage bucket
            storage_cleared = 0
            try:
                files = self.client.storage.from_(self.STORAGE_BUCKET).list()
                for folder in files:
                    if folder.get("name"):
                        folder_files = self.client.storage.from_(self.STORAGE_BUCKET).list(folder["name"])
                        for file in folder_files:
                            if file.get("name"):
                                self.client.storage.from_(self.STORAGE_BUCKET).remove([f"{folder['name']}/{file['name']}"])
                                storage_cleared += 1
            except Exception as e:
                print(f"[Clear Storage] Warning: {e}")
            
            return {
                "success": True,
                "stories_deleted": stories_deleted,
                "chapters_deleted": chapters_deleted,
                "storage_files_cleared": storage_cleared
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
db = Database()

