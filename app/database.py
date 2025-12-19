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
        """Bulk insert/update chapters"""
        result = self.client.table("chapters").upsert(
            chapters,
            on_conflict="story_id,chapter_number"
        ).execute()
        return result.data or []
    
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


# Singleton instance
db = Database()
