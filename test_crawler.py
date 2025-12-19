"""
Test Script for Crawler
Run this to verify the crawler is working correctly
"""
import asyncio
import json
from app.crawler.crawler import StoryCrawler, crawl_story


async def test_crawl_story():
    """Test crawling a single story"""
    print("=" * 60)
    print("🧪 TEST: Crawl Single Story")
    print("=" * 60)
    
    url = "https://truyenfull.vision/tam-quoc-dien-nghia/"
    
    print(f"\n📖 Target: {url}")
    print("⏳ Starting crawl (this may take 30-60 seconds)...\n")
    
    try:
        story = await crawl_story(url, include_chapters=False)
        
        print("\n✅ SUCCESS! Story data:")
        print("-" * 40)
        print(f"Title:    {story.get('title')}")
        print(f"Author:   {story.get('author')}")
        print(f"Status:   {story.get('status')}")
        print(f"Genres:   {', '.join(story.get('genres', []))}")
        print(f"Chapters: {story.get('total_chapters')}")
        print(f"Cover:    {story.get('cover_url', 'N/A')[:50]}...")
        print("-" * 40)
        
        # Save to file
        output_file = "test_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(story, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Full data saved to: {output_file}")
        
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crawl_list():
    """Test crawling story list"""
    print("\n" + "=" * 60)
    print("🧪 TEST: Crawl Story List (Hot Stories)")
    print("=" * 60)
    
    print("\n⏳ Crawling 1 page of hot stories...\n")
    
    try:
        crawler = StoryCrawler()
        stories = await crawler.crawl_hot_stories(max_pages=1)
        
        print(f"\n✅ SUCCESS! Found {len(stories)} stories:")
        print("-" * 40)
        
        for i, story in enumerate(stories[:5], 1):
            print(f"{i}. {story.get('title', 'Unknown')}")
            print(f"   Author: {story.get('author', 'N/A')}")
            print(f"   URL: {story.get('source_url', 'N/A')}")
            print()
        
        if len(stories) > 5:
            print(f"... and {len(stories) - 5} more")
        
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "🚀 CRAWLER SERVICE - TEST SUITE" + "\n")
    
    results = []
    
    # Test 1: Single story
    results.append(("Crawl Single Story", await test_crawl_story()))
    
    # Test 2: Story list
    # results.append(("Crawl Story List", await test_crawl_list()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
