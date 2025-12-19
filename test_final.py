#!/usr/bin/env python
"""Direct test final version"""
import asyncio
import sys
sys.path.append('.')

async def test():
    from app.crawler.crawler import StoryCrawler
    from app.database import Database
    
    crawler = StoryCrawler()
    db = Database()
    
    url = "https://truyenfull.vision/tam-quoc-dien-nghia/"
    
    print("🔥 TESTING FINAL VERSION\n")
    story = await crawler.crawl_story(url, include_chapters=False)
    
    print(f"\n{'='*60}")
    print(f"✅ CRAWL SUCCESSFUL!")
    print(f"Title: {story['title']}")
    print(f"Total Chapters: {story['total_chapters']}")
    print(f"Cover: {'✅' if story.get('cover_url') else '❌'}")
    
    # Save to DB
    print(f"\n💾 Saving to database...")
    from datetime import datetime, timezone
    
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
    
    saved = await db.upsert_story(story_record)
    print(f"✅ Saved! ID: {saved.get('id', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test())
