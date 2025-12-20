"""
API Routes v1 - Full Reader & Crawler APIs
Following the Frontend API Specification
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query

from ..database import Database
from ..schemas.story import (
    TaskStatus,
    HealthResponse,
)
from ..crawler.crawler import StoryCrawler
from .dependencies import get_db


router = APIRouter()


# ========== Health Check ==========

@router.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """API health check"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )


# ==========================================================================
# PHẦN 1: CRAWLER API (Dành cho Admin/Tool)
# ==========================================================================

@router.post("/api/v1/crawler/init", tags=["Crawler"])
async def init_crawl(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    1. Kích hoạt cào truyện mới (Init Crawl)
    
    Body: {"url": "https://truyenfull.vision/ten-truyen", "source": "truyenfull"}
    """
    url = request.get("url")
    source = request.get("source", "truyenfull")
    crawl_chapters = request.get("crawl_chapters", True)  # Mặc định crawl nội dung
    
    if not url:
        raise HTTPException(status_code=400, detail="Thiếu URL truyện")
    
    # Tạo task ID
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    task_data = {
        "id": task_id,
        "story_url": url,
        "status": "processing",
        "progress": 0,
        "message": "Đang khởi tạo...",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        await db.create_task(task_data)
    except Exception as e:
        print(f"Warning: Could not create task: {e}")
    
    # Chạy crawl trong background process độc lập (Fix lỗi Asyncio Windows)
    import subprocess
    import sys
    
    cmd = [
        sys.executable, 
        "-m", 
        "app.crawler.runner", 
        task_id, 
        url, 
        str(crawl_chapters)
    ]
    
    # Popen chạy process không chờ (non-blocking)
    subprocess.Popen(cmd)
    
    return {
        "status": 200,
        "message": "Đã tiếp nhận yêu cầu. Đang xử lý ngầm (Subprocess).",
        "task_id": task_id
    }


@router.get("/api/v1/crawler/tasks/{task_id}", tags=["Crawler"])
async def check_crawl_status(task_id: str, db: Database = Depends(get_db)):
    """
    2. Kiểm tra tiến độ cào (Check Status)
    """
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại")
    
    status = task.get("status", "unknown")
    
    if status == "processing":
        return {
            "status": "processing",
            "progress": task.get("message", "Đang xử lý..."),
            "percent": task.get("progress", 0)
        }
    elif status == "completed":
        return {
            "status": "completed",
            "novel_id": task.get("novel_id"),
            "total_chapters": task.get("total_chapters", 0)
        }
    else:  # failed
        return {
            "status": "failed",
            "error": task.get("error", "Lỗi không xác định")
        }


@router.post("/api/v1/crawler/update/{novel_id}", tags=["Crawler"])
async def update_novel(
    novel_id: str,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    3. Cập nhật chương mới (Update Novel)
    """
    # Get story from DB
    story = await db.get_story_by_id(novel_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")
    
    # TODO: Implement update logic
    return {
        "status": "success",
        "new_chapters_added": 0,
        "message": "Đang phát triển tính năng này..."
    }


@router.post("/api/v1/crawler/bulk-crawl", tags=["Crawler"])
async def bulk_crawl(
    request: dict,
    db: Database = Depends(get_db)
):
    """
    Crawl toàn bộ truyện từ các trang danh sách
    
    Body: {
        "categories": ["hot", "new", "completed"],  // Các danh mục cần crawl
        "max_pages": 5,  // Số trang tối đa mỗi danh mục
        "crawl_chapters": true  // Có crawl nội dung chương không
    }
    """
    categories = request.get("categories", ["hot", "new", "completed"])
    max_pages = request.get("max_pages", 5)
    crawl_chapters = request.get("crawl_chapters", True)
    
    # Tạo bulk task ID
    bulk_task_id = f"bulk_{uuid.uuid4().hex[:12]}"
    
    import subprocess
    import sys
    
    cmd = [
        sys.executable,
        "-m",
        "app.crawler.bulk_runner",
        bulk_task_id,
        ",".join(categories),
        str(max_pages),
        str(crawl_chapters)
    ]
    
    subprocess.Popen(cmd)
    
    return {
        "status": 200,
        "message": f"Đã bắt đầu crawl hàng loạt. Categories: {categories}, Max pages: {max_pages}",
        "bulk_task_id": bulk_task_id
    }


# ==========================================================================
# SCHEDULER CONTROL API (Auto-crawl & Manual crawl)
# ==========================================================================

from ..scheduler import scheduler

@router.get("/api/v1/scheduler/status", tags=["Scheduler"])
async def get_scheduler_status():
    """Lấy trạng thái scheduler"""
    return scheduler.get_status()


@router.post("/api/v1/scheduler/auto/start", tags=["Scheduler"])
async def start_auto_crawl():
    """Bật auto-crawl (mỗi 15 phút)"""
    result = await scheduler.start_auto_crawl()
    return result


@router.post("/api/v1/scheduler/auto/stop", tags=["Scheduler"])
async def stop_auto_crawl():
    """Tắt auto-crawl"""
    result = scheduler.stop_auto_crawl()
    return result


@router.post("/api/v1/scheduler/manual", tags=["Scheduler"])
async def trigger_manual_crawl(request: dict, background_tasks: BackgroundTasks):
    """
    Chạy crawl thủ công (chạy liên tục cho đến khi xong)
    
    Body: {
        "categories": ["hot", "new", "completed"],
        "max_pages": 5
    }
    """
    categories = request.get("categories", ["new"])
    max_pages = request.get("max_pages", 2)
    
    # Chạy trong background
    background_tasks.add_task(scheduler.manual_crawl, categories, max_pages)
    
    return {
        "status": "started",
        "message": f"Manual crawl started: {categories}, {max_pages} pages each"
    }


# ==========================================================================
# PHẦN 2: READER API (Dành cho Web đọc truyện)
# ==========================================================================

@router.get("/api/v1/novels", tags=["Reader"])
async def get_novels(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("newest", regex="^(newest|popular)$"),
    db: Database = Depends(get_db)
):
    """
    4. Lấy danh sách truyện (Home Page / Filter)
    """
    offset = (page - 1) * limit
    stories = await db.get_stories(limit=limit, offset=offset)
    
    # Format response
    data = []
    for s in stories:
        data.append({
            "id": s.get("id"),
            "title": s.get("title"),
            "author": s.get("author"),
            "cover_url": s.get("cover_url"),
            "latest_chapter": s.get("total_chapters", 0),
            "status": s.get("status", "Đang ra")
        })
    
    total = len(data)  # TODO: Get actual total count
    
    return {
        "data": data,
        "pagination": {
            "total_items": total,
            "total_pages": max(1, (total + limit - 1) // limit),
            "current_page": page
        }
    }


@router.get("/api/v1/novels/{novel_id}", tags=["Reader"])
async def get_novel_detail(novel_id: str, db: Database = Depends(get_db)):
    """
    5. Xem thông tin chi tiết truyện (Novel Detail)
    """
    story = await db.get_story_by_id(novel_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")
    
    return {
        "id": story.get("id"),
        "title": story.get("title"),
        "description": story.get("description"),
        "author": story.get("author"),
        "cover_url": story.get("cover_url"),
        "source_url": story.get("source_url"),
        "status": story.get("status", "Đang ra"),
        "total_chapters": story.get("total_chapters", 0),
        "categories": story.get("genres", [])
    }


@router.get("/api/v1/novels/{novel_id}/chapters", tags=["Reader"])
async def get_chapter_list(
    novel_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Database = Depends(get_db)
):
    """
    6. Lấy danh sách chương (Chapter List)
    """
    story = await db.get_story_by_id(novel_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")
    
    offset = (page - 1) * limit
    chapters = await db.get_chapters_by_story(novel_id, limit=limit, offset=offset)
    
    data = []
    for ch in chapters:
        data.append({
            "id": ch.get("id"),
            "chapter_number": ch.get("chapter_number"),
            "title": ch.get("title"),
            "source_url": ch.get("source_url"),
            "created_at": ch.get("created_at"),
        })
    
    return {
        "data": data,
        "total_chapters": story.get("total_chapters", 0)
    }


@router.get("/api/v1/chapters/{chapter_id}", tags=["Reader"])
async def read_chapter(chapter_id: str, db: Database = Depends(get_db)):
    """
    7. Đọc nội dung chương (Read Chapter)
    Storage-first: Check Storage -> DB -> Crawl from source
    Saves new content to Storage (GZIP compressed)
    """
    chapter = await db.get_chapter_by_id(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chương không tồn tại")
    
    story_id = chapter.get("story_id")
    chapter_num = chapter.get("chapter_number", 0)
    content = ""
    
    # Step 1: Try Storage first (GZIP compressed)
    if chapter.get("is_archived"):
        content = await db.download_chapter_content(story_id, chapter_num)
        if content:
            print(f"[Chapter] Loaded from Storage: {chapter.get('title')}")
    
    # Step 2: Fallback to DB column (legacy)
    if not content:
        content = chapter.get("content", "")
        if content:
            print(f"[Chapter] Loaded from DB column: {chapter.get('title')}")
    
    # Step 3: Crawl from source if still no content
    if not content and chapter.get("source_url"):
        try:
            import httpx
            from ..crawler.parsers import parse_chapter_content
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
                "Referer": "https://truyenfull.vision/",
            }
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
                print(f"[Chapter] Crawling from source: {chapter['source_url']}")
                response = await client.get(chapter["source_url"])
                response.raise_for_status()
                
                parsed = parse_chapter_content(response.text, chapter["source_url"])
                content = parsed.get("content", "")
                
                # Save to Storage (GZIP) instead of DB
                if content:
                    success = await db.upload_chapter_content(story_id, chapter_num, content)
                    if success:
                        print(f"[Chapter] Saved to Storage: {chapter.get('title')}")
                    else:
                        # Fallback: save to DB if storage fails
                        await db.upsert_chapter({
                            "story_id": story_id,
                            "chapter_number": chapter_num,
                            "title": chapter["title"],
                            "source_url": chapter["source_url"],
                            "content": content,
                        })
                        print(f"[Chapter] Saved to DB (fallback): {chapter.get('title')}")
        except Exception as e:
            print(f"[Chapter ERROR] Fetching failed: {e}")
            content = f"Lỗi tải nội dung: {str(e)}"
    
    # Get prev/next chapters
    prev_chapter = await db.get_chapter(story_id, chapter_num - 1)
    next_chapter = await db.get_chapter(story_id, chapter_num + 1)
    
    return {
        "id": chapter.get("id"),
        "novel_id": story_id,
        "chapter_number": chapter_num,
        "title": chapter.get("title"),
        "content": content,
        "is_archived": chapter.get("is_archived", False),
        "navigation": {
            "prev_chapter_id": prev_chapter.get("id") if prev_chapter else None,
            "next_chapter_id": next_chapter.get("id") if next_chapter else None
        }
    }


from fastapi import BackgroundTasks

@router.post("/api/v1/novels/{story_id}/sync-offline", tags=["Reader"])
async def sync_story_offline(
    story_id: str, 
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    9. Tải Offline toàn bộ nội dung truyện (Sync Offline)
    Crawl và lưu tất cả chapters vào Storage (GZIP nén)
    Chạy nền để không block response
    """
    story = await db.get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")
    
    # Get all chapters that need syncing (not yet archived)
    chapters = await db.get_chapters_by_story(story_id, limit=10000)
    chapters_to_sync = [c for c in chapters if not c.get("is_archived")]
    
    if not chapters_to_sync:
        return {
            "message": "Đã có sẵn offline!",
            "story_id": story_id,
            "total_chapters": len(chapters),
            "already_archived": len(chapters),
            "to_sync": 0
        }
    
    # Start background sync task
    async def sync_chapters_task():
        import httpx
        from ..crawler.parsers import parse_chapter_content
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9",
            "Referer": "https://truyenfull.vision/",
        }
        
        synced = 0
        errors = 0
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            for i, chapter in enumerate(chapters_to_sync):
                try:
                    # Fetch content
                    response = await client.get(chapter["source_url"])
                    response.raise_for_status()
                    
                    parsed = parse_chapter_content(response.text, chapter["source_url"])
                    content = parsed.get("content", "")
                    
                    if content:
                        # Upload to Storage
                        success = await db.upload_chapter_content(
                            chapter["story_id"], 
                            chapter["chapter_number"], 
                            content
                        )
                        if success:
                            synced += 1
                    
                    # Rate limiting - 0.5s between requests
                    if i < len(chapters_to_sync) - 1:
                        import asyncio
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    print(f"[Sync ERROR] Chapter {chapter.get('chapter_number')}: {e}")
                    errors += 1
                
                # Log progress every 50 chapters
                if (i + 1) % 50 == 0:
                    print(f"[Sync] Progress: {i+1}/{len(chapters_to_sync)} (synced: {synced}, errors: {errors})")
        
        print(f"[Sync COMPLETE] Story {story_id}: {synced}/{len(chapters_to_sync)} chapters synced")
    
    # Run in background
    background_tasks.add_task(sync_chapters_task)
    
    return {
        "message": "Đang tải offline...",
        "story_id": story_id,
        "story_title": story.get("title"),
        "total_chapters": len(chapters),
        "already_archived": len(chapters) - len(chapters_to_sync),
        "to_sync": len(chapters_to_sync),
        "status": "processing"
    }


@router.get("/api/v1/novels/{story_id}/offline-status", tags=["Reader"])
async def get_offline_status(story_id: str, db: Database = Depends(get_db)):
    """
    10. Kiểm tra trạng thái offline của truyện
    """
    story = await db.get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Truyện không tồn tại")
    
    chapters = await db.get_chapters_by_story(story_id, limit=10000)
    archived_count = sum(1 for c in chapters if c.get("is_archived"))
    
    return {
        "story_id": story_id,
        "story_title": story.get("title"),
        "total_chapters": len(chapters),
        "archived_chapters": archived_count,
        "percent_complete": round(archived_count / len(chapters) * 100, 1) if chapters else 0,
        "is_complete": archived_count == len(chapters)
    }


@router.get("/api/v1/search", tags=["Reader"])
async def search_novels(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db)
):
    """
    8. Tìm kiếm truyện (Search)
    """
    results = await db.search_stories(q, limit=limit)
    
    data = []
    for s in results:
        data.append({
            "id": s.get("id"),
            "title": s.get("title"),
            "author": s.get("author"),
            "cover_url": s.get("cover_url"),
            "latest_chapter": s.get("total_chapters", 0),
            "status": s.get("status", "Đang ra")
        })
    
    return {
        "data": data,
        "pagination": {
            "total_items": len(data),
            "total_pages": 1,
            "current_page": page
        }
    }


# ==========================================================================
# ADMIN DASHBOARD
# ==========================================================================

from fastapi.responses import HTMLResponse

@router.get("/admin/dashboard", response_class=HTMLResponse, tags=["Admin"])
async def admin_dashboard():
    """Dashboard quản lý crawl"""
    html_content = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crawler Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .section h2 {
            margin-bottom: 15px;
            font-size: 1.5rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        th {
            background: rgba(255, 255, 255, 0.1);
            font-weight: 600;
        }
        .status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .status.completed { background: #10b981; }
        .status.processing { background: #f59e0b; }
        .status.failed { background: #ef4444; }
        .refresh-info {
            text-align: center;
            opacity: 0.7;
            margin-top: 20px;
            font-size: 0.9rem;
        }
        .btn {
            background: #10b981;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn:hover { background: #059669; transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕷️ Crawler Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📚 Tổng Truyện</h3>
                <div class="value" id="total-stories">-</div>
            </div>
            <div class="stat-card">
                <h3>📄 Tổng Chương</h3>
                <div class="value" id="total-chapters">-</div>
            </div>
            <div class="stat-card">
                <h3>⚡ Tasks Hoàn Thành</h3>
                <div class="value" id="completed-tasks">-</div>
            </div>
            <div class="stat-card">
                <h3>🔄 Đang Xử Lý</h3>
                <div class="value" id="processing-tasks">-</div>
            </div>
        </div>

        <div class="section">
            <h2>📖 Truyện Mới Nhất</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tên Truyện</th>
                        <th>Tác Giả</th>
                        <th>Số Chương</th>
                        <th>Trạng Thái</th>
                    </tr>
                </thead>
                <tbody id="recent-stories">
                    <tr><td colspan="4">Đang tải...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🔧 Tasks Gần Đây</h2>
            <table>
                <thead>
                    <tr>
                        <th>Task ID</th>
                        <th>URL</th>
                        <th>Trạng Thái</th>
                        <th>Tiến Độ</th>
                    </tr>
                </thead>
                <tbody id="recent-tasks">
                    <tr><td colspan="4">Đang tải...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="refresh-info">⏱️ Auto-refresh mỗi 3 giây</div>
    </div>

    <script>
        async function loadStats() {
            try {
                const res = await fetch('/admin/stats');
                const data = await res.json();
                
                document.getElementById('total-stories').textContent = data.total_stories;
                document.getElementById('total-chapters').textContent = data.total_chapters;
                document.getElementById('completed-tasks').textContent = data.completed_tasks;
                document.getElementById('processing-tasks').textContent = data.processing_tasks;
                
                // Recent stories
                const storiesHtml = data.recent_stories.map(s => `
                    <tr>
                        <td>${s.title}</td>
                        <td>${s.author || 'N/A'}</td>
                        <td>${s.total_chapters}</td>
                        <td><span class="status completed">${s.status}</span></td>
                    </tr>
                `).join('');
                document.getElementById('recent-stories').innerHTML = storiesHtml || '<tr><td colspan="4">Chưa có dữ liệu</td></tr>';
                
                // Recent tasks
                const tasksHtml = data.recent_tasks.map(t => `
                    <tr>
                        <td>${t.id.substring(0, 12)}...</td>
                        <td>${t.story_url.substring(0, 50)}...</td>
                        <td><span class="status ${t.status}">${t.status}</span></td>
                        <td>${t.progress}%</td>
                    </tr>
                `).join('');
                document.getElementById('recent-tasks').innerHTML = tasksHtml || '<tr><td colspan="4">Chưa có tasks</td></tr>';
            } catch (err) {
                console.error('Error loading stats:', err);
            }
        }
        
        loadStats();
        setInterval(loadStats, 3000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.get("/admin/stats", tags=["Admin"])
async def admin_stats(db: Database = Depends(get_db)):
    """API lấy stats cho dashboard"""
    try:
        # Total stories & chapters (Supabase Python client is SYNC, not async)
        total_stories_result = db.client.table("stories").select("id", count="exact").execute()
        total_stories = total_stories_result.count or 0
        
        total_chapters_result = db.client.table("chapters").select("id", count="exact").execute()
        total_chapters = total_chapters_result.count or 0
        
        # Recent stories
        recent_stories_result = db.client.table("stories").select("*").order("created_at", desc=True).limit(5).execute()
        recent_stories = recent_stories_result.data or []
        
        # Tasks stats
        completed_tasks_result = db.client.table("crawl_tasks").select("id", count="exact").eq("status", "completed").execute()
        completed_tasks = completed_tasks_result.count or 0
        
        processing_tasks_result = db.client.table("crawl_tasks").select("id", count="exact").eq("status", "processing").execute()
        processing_tasks = processing_tasks_result.count or 0
        
        # Recent tasks
        recent_tasks_result = db.client.table("crawl_tasks").select("*").order("created_at", desc=True).limit(5).execute()
        recent_tasks = recent_tasks_result.data or []
        
        return {
            "total_stories": total_stories,
            "total_chapters": total_chapters,
            "completed_tasks": completed_tasks,
            "processing_tasks": processing_tasks,
            "recent_stories": recent_stories,
            "recent_tasks": recent_tasks
        }
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        # Return default values if error
        return {
            "total_stories": 0,
            "total_chapters": 0,
            "completed_tasks": 0,
            "processing_tasks": 0,
            "recent_stories": [],
            "recent_tasks": []
        }


# ==========================================================================
# LEGACY/QUICK TEST ENDPOINTS
# ==========================================================================

@router.get("/api/preview/{slug}", tags=["Debug"])
async def preview_story(slug: str):
    """Quick preview - crawl without saving to DB"""
    url = f"https://truyenfull.vision/{slug}/"
    
    try:
        crawler = StoryCrawler()
        story = await crawler.crawl_story(url, include_chapters=False)
        return story
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
