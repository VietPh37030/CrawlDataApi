# 🕷️ Truyện Crawler Service

Modern, scalable web crawler for **truyenfull.vision** with full Reader API.

## 🏗️ Architecture

```
User → POST /crawler/init → Redis Queue → Celery Worker → Supabase DB
                                               ↓
                                        Playwright Browser
                                               ↓
User ← GET /novels ← FastAPI ← Supabase DB
```

## 🚀 Quick Start

### 1. Setup Supabase Database

**Copy nội dung file `supabase_schema.sql` vào Supabase SQL Editor và chạy!**

```sql
-- Xem file: supabase_schema.sql
```

### 2. Run Locally

```powershell
cd d:\Ark_3\crawler-service
.\venv\Scripts\activate

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open Swagger UI

**http://localhost:8000/docs**

---

## 📚 API Documentation

**Base URL**: `http://localhost:8000/api/v1`

### PHẦN 1: CRAWLER API (Admin/Tool)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/crawler/init` | Kích hoạt cào truyện mới |
| GET | `/crawler/tasks/{task_id}` | Kiểm tra tiến độ cào |
| POST | `/crawler/update/{novel_id}` | Cập nhật chương mới |

#### 1. Kích hoạt cào (Init Crawl)

```bash
curl -X POST http://localhost:8000/api/v1/crawler/init \
  -H "Content-Type: application/json" \
  -d '{"url": "https://truyenfull.vision/tam-quoc-dien-nghia/", "source": "truyenfull"}'
```

Response:
```json
{
  "status": 200,
  "message": "Đã tiếp nhận yêu cầu. Đang xử lý ngầm.",
  "task_id": "task_abc123_xyz"
}
```

#### 2. Check tiến độ

```bash
curl http://localhost:8000/api/v1/crawler/tasks/task_abc123_xyz
```

Response (đang chạy):
```json
{
  "status": "processing",
  "progress": "Đang tải chương 50/1200...",
  "percent": 4
}
```

Response (hoàn thành):
```json
{
  "status": "completed",
  "novel_id": "uuid-cua-truyen",
  "total_chapters": 1200
}
```

---

### PHẦN 2: READER API (Web đọc truyện)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/novels` | Danh sách truyện |
| GET | `/novels/{id}` | Chi tiết truyện |
| GET | `/novels/{id}/chapters` | Danh sách chương |
| GET | `/chapters/{id}` | Nội dung chương |
| GET | `/search?q=...` | Tìm kiếm |

#### 4. Danh sách truyện

```bash
curl "http://localhost:8000/api/v1/novels?page=1&limit=20&sort=newest"
```

#### 5. Chi tiết truyện

```bash
curl "http://localhost:8000/api/v1/novels/{novel_id}"
```

#### 6. Danh sách chương

```bash
curl "http://localhost:8000/api/v1/novels/{novel_id}/chapters?page=1&limit=50"
```

#### 7. Đọc nội dung chương

```bash
curl "http://localhost:8000/api/v1/chapters/{chapter_id}"
```

Response:
```json
{
  "id": "chap-uuid",
  "novel_id": "novel-uuid",
  "chapter_number": 2,
  "title": "Chương 2: Xuống núi",
  "content": "<p>Nội dung truyện...</p>",
  "navigation": {
    "prev_chapter_id": "chap-uuid-1",
    "next_chapter_id": "chap-uuid-3"
  }
}
```

#### 8. Tìm kiếm

```bash
curl "http://localhost:8000/api/v1/search?q=tam%20quoc"
```

---

## 📁 Project Structure

```
crawler-service/
├── app/
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings
│   ├── database.py      # Supabase client
│   ├── api/routes.py    # All API endpoints
│   ├── crawler/
│   │   ├── crawler.py   # Main crawler + chapter content
│   │   ├── browser.py   # Playwright manager
│   │   ├── parsers.py   # HTML parsers
│   │   └── stealth.py   # Anti-detection
│   └── schemas/
├── workers/             # Celery tasks
├── supabase_schema.sql  # Database schema
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🔒 Anti-Bot Features

- ✅ Random delays (3-10 seconds)
- ✅ User-Agent rotation
- ✅ Playwright stealth mode
- ✅ Human-like behavior simulation
- ✅ Resource blocking (images/fonts)

## 📄 License

MIT License
