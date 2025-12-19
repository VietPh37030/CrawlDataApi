# 📚 API DOCUMENTATION - WEB ĐỌC TRUYỆN

**Base URL**: `http://localhost:8000/api/v1`  
**Production**: `https://your-domain.com/api/v1`

---

## 📖 MỤC LỤC

1. [Reader API](#reader-api) - API cho người đọc
2. [Crawler API](#crawler-api) - API quản trị
3. [Database Schema](#database-schema)
4. [Error Codes](#error-codes)

---

## 🎯 READER API (Dành cho Frontend)

### 1. Lấy Danh Sách Truyện

**Endpoint**: `GET /novels`

**Query Parameters**:
- `page` (int, default=1): Số trang
- `limit` (int, default=20): Số truyện mỗi trang
- `sort` (string): `newest` hoặc `popular`

**Request Example**:
```bash
GET /api/v1/novels?page=1&limit=20&sort=newest
```

**Response**:
```json
{
  "data": [
    {
      "id": "uuid-123",
      "title": "Tên Truyện",
      "author": "Tác Giả",
      "cover_url": "https://...",
      "latest_chapter": 100,
      "status": "Đang ra" // hoặc "Full"
    }
  ],
  "pagination": {
    "total_items": 500,
    "total_pages": 25,
    "current_page": 1
  }
}
```

---

### 2. Chi Tiết Truyện

**Endpoint**: `GET /novels/{novel_id}`

**Request Example**:
```bash
GET /api/v1/novels/a71ca284-4841-405f-b20c-78c742208fa1
```

**Response**:
```json
{
  "id": "uuid-123",
  "title": "Tên Truyện",
  "description": "Mô tả truyện...",
  "author": "Tác Giả",
  "cover_url": "https://...",
  "source_url": "https://truyenfull.vision/...",
  "status": "Full",
  "total_chapters": 1200,
  "categories": ["Tiên Hiệp", "Huyền Huyễn"]
}
```

---

### 3. Danh Sách Chương

**Endpoint**: `GET /novels/{novel_id}/chapters`

**Query Parameters**:
- `page` (int, default=1)
- `limit` (int, default=50)

**Request Example**:
```bash
GET /api/v1/novels/{novel_id}/chapters?page=1&limit=50
```

**Response**:
```json
{
  "data": [
    {
      "id": "chapter-uuid-1",
      "chapter_number": 1,
      "title": "Chương 1: Khởi đầu"
    },
    {
      "id": "chapter-uuid-2",
      "chapter_number": 2,
      "title": "Chương 2: Tu luyện"
    }
  ],
  "total_chapters": 1200
}
```

---

### 4. Đọc Nội Dung Chương ⭐

**Endpoint**: `GET /chapters/{chapter_id}`

**Request Example**:
```bash
GET /api/v1/chapters/6da95c8b-3ecf-49e5-8863-211fa9bf5f1c
```

**Response**:
```json
{
  "id": "chapter-uuid-2",
  "novel_id": "novel-uuid",
  "chapter_number": 2,
  "title": "Chương 2: Tu luyện",
  "content": "Nội dung đầy đủ của chương...\n\nNội dung có thể dài hàng nghìn ký tự...",
  "navigation": {
    "prev_chapter_id": "chapter-uuid-1",
    "next_chapter_id": "chapter-uuid-3"
  }
}
```

**⚠️ Lưu ý**: 
- `content` chứa **toàn bộ text** chương (20KB - 50KB)
- Paragraphs ngăn cách bởi `\n\n`

---

### 5. Tìm Kiếm

**Endpoint**: `GET /search`

**Query Parameters**:
- `q` (string, required): Từ khóa tìm kiếm
- `page` (int, default=1)
- `limit` (int, default=20)

**Request Example**:
```bash
GET /api/v1/search?q=tam%20quoc
```

**Response**: Giống format `/novels`

---

## 🔧 CRAWLER API (Dành cho Admin)

### 1. Trigger Crawl 1 Truyện

**Endpoint**: `POST /crawler/init`

**Body**:
```json
{
  "url": "https://truyenfull.vision/ten-truyen/",
  "source": "truyenfull",
  "crawl_chapters": true
}
```

**Response**:
```json
{
  "status": 200,
  "message": "Đã tiếp nhận yêu cầu. Đang xử lý ngầm.",
  "task_id": "task_abc123"
}
```

---

### 2. Check Tiến Độ Crawl

**Endpoint**: `GET /crawler/tasks/{task_id}`

**Response (đang chạy)**:
```json
{
  "status": "processing",
  "progress": "Đang tải chương 50/1200...",
  "percent": 4
}
```

**Response (hoàn thành)**:
```json
{
  "status": "completed",
  "novel_id": "uuid-cua-truyen",
  "total_chapters": 1200
}
```

---

### 3. Crawl Toàn Bộ (Bulk)

**Endpoint**: `POST /crawler/bulk-crawl`

**Body**:
```json
{
  "categories": ["hot", "new", "completed"],
  "max_pages": 10,
  "crawl_chapters": true
}
```

**Response**:
```json
{
  "status": 200,
  "message": "Đã bắt đầu crawl hàng loạt...",
  "bulk_task_id": "bulk_xyz789"
}
```

---

## 🗄️ DATABASE SCHEMA

### Table: `stories`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `slug` | TEXT | URL slug (unique) |
| `title` | TEXT | Tên truyện |
| `author` | TEXT | Tác giả |
| `description` | TEXT | Mô tả |
| `genres` | TEXT[] | Thể loại (array) |
| `status` | TEXT | "Đang ra" / "Full" |
| `total_chapters` | INTEGER | Tổng số chương |
| `cover_url` | TEXT | Link ảnh bìa |
| `source_url` | TEXT | Link gốc |
| `created_at` | TIMESTAMPTZ | Ngày tạo |
| `updated_at` | TIMESTAMPTZ | Ngày cập nhật |

### Table: `chapters`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `story_id` | UUID | Foreign key → stories |
| `chapter_number` | INTEGER | Số chương |
| `title` | TEXT | Tiêu đề chương |
| `content` | TEXT | **Nội dung đầy đủ** |
| `source_url` | TEXT | Link gốc |
| `created_at` | TIMESTAMPTZ | Ngày tạo |

**Unique**: `(story_id, chapter_number)`

---

## ⚠️ ERROR CODES

| HTTP Code | Meaning |
|-----------|---------|
| `200` | Success |
| `400` | Bad Request (thiếu params) |
| `404` | Not Found (truyện/chương không tồn tại) |
| `500` | Internal Server Error |

**Error Response Format**:
```json
{
  "detail": "Truyện không tồn tại"
}
```

---

## 🚀 SAMPLE FLOW CHO FRONTEND

### Flow 1: Hiển thị trang chủ

1. `GET /novels?page=1&limit=20&sort=newest`
2. Render danh sách truyện
3. Click vào truyện → `GET /novels/{id}`

### Flow 2: Đọc truyện

1. `GET /novels/{id}/chapters?page=1`
2. User chọn chương
3. `GET /chapters/{chapter_id}` → Hiển thị `content`
4. Dùng `navigation.next_chapter_id` để đọc tiếp

---

## 📊 DASHBOARD ADMIN

**URL**: `http://localhost:8000/admin/dashboard`

- Xem số liệu realtime
- Theo dõi tiến độ crawl
- Auto-refresh mỗi 3 giây

---

## 🔗 USEFUL LINKS

- API Docs (Swagger): `http://localhost:8000/docs`
- Dashboard: `http://localhost:8000/admin/dashboard`
- Health Check: `http://localhost:8000/`

---

**Lưu ý cho FE**:
1. Tất cả response dạng JSON
2. Pagination luôn có format: `{data: [], pagination: {}}`
3. Content chương có thể rất dài (20KB+), nên dùng lazy load
4. `next_chapter_id` / `prev_chapter_id` có thể null (chương đầu/cuối)
