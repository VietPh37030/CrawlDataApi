# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER + KEEP-ALIVE 24/7

## BƯỚC 1: Chuẩn Bị Git

```bash
cd d:\Ark_3\crawler-service
git init
git add .
git commit -m "Initial commit: Crawler service"
```

**Push lên GitHub:**
```bash
git remote add origin https://github.com/username/crawler-service.git
git branch -M main
git push -u origin main
```

---

## BƯỚC 2: Deploy lên Render

### 2.1. Tạo Web Service
1. Vào https://render.com → **New** → **Web Service**
2. Connect GitHub repo: `crawler-service`
3. Cấu hình:

| Field | Value |
|-------|-------|
| **Name** | `truyen-crawler` |
| **Region** | Singapore (gần VN nhất) |
| **Branch** | `main` |
| **Root Directory** | (để trống) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && bash build.sh` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | **Free** |

### 2.2. Environment Variables
Add vào Render:

```
SUPABASE_URL=https://jkztbrvdcceqibaanmed.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...
BASE_URL=https://truyenfull.vision
DEBUG=false
```

### 2.3. Deploy
Click **Create Web Service** → Đợi 5-10 phút

URL của bạn: `https://truyen-crawler.onrender.com`

---

## BƯỚC 3: Keep-Alive 24/7 (UptimeRobot)

### 3.1. Tạo Tài Khoản
1. Vào https://uptimerobot.com
2. Sign up miễn phí (50 monitors)

### 3.2. Tạo Monitor
1. Click **Add New Monitor**
2. Cấu hình:

| Field | Value |
|-------|-------|
| **Monitor Type** | HTTP(s) |
| **Friendly Name** | `Truyen Crawler Keep-Alive` |
| **URL** | `https://truyen-crawler.onrender.com/` |
| **Monitoring Interval** | `5 minutes` |

3. Click **Create Monitor**

### 3.3. Kết Quả
- UptimeRobot sẽ ping vào API mỗi 5 phút
- Render không bao giờ sleep
- Chạy 24/7 hoàn toàn miễn phí ✅

---

## BƯỚC 4: Test Deployment

```bash
# Health check
curl https://truyen-crawler.onrender.com/

# Crawl 1 truyện
curl -X POST https://truyen-crawler.onrender.com/api/v1/crawler/init \
  -H "Content-Type: application/json" \
  -d '{"url":"https://truyenfull.vision/tam-quoc-dien-nghia/","crawl_chapters":true}'

# Xem dashboard
https://truyen-crawler.onrender.com/admin/dashboard
```

---

## 🎯 Chiến Lược Tối Ưu

### RAM Management (512MB)
✅ **Đã tối ưu** trong `browser.py`:
- `--single-process`
- `--disable-gpu`
- Window size nhỏ (1280x720)

### Quota 750h/tháng
- **Backend** (Render): 744h/tháng
- **Frontend** (Vercel): Free không giới hạn
- **Database** (Supabase): Free riêng

### Performance
- **Render Free**: Cold start 30s đầu tiên
- **UptimeRobot**: Giữ server "nóng" mọi lúc
- **Crawler**: Chạy background, không ảnh hưởng API

---

## 📦 Frontend Deployment (Vercel)

Sau khi xong Backend, deploy FE:

1. Push React/Vue code lên GitHub
2. Vào https://vercel.com
3. Import project
4. Environment Variables:
```
VITE_API_URL=https://truyen-crawler.onrender.com
```
5. Deploy (< 1 phút)

URL: `https://truyen-web.vercel.app`

---

## ⚠️ Lưu Ý

1. **First Load**: Render free có cold start ~30s
2. **RAM**: Nếu crawl quá nhiều cùng lúc → có thể crash → tự restart
3. **Logs**: Xem logs tại Render Dashboard
4. **Keep-alive**: PHẢI setup UptimeRobot, không thì sleep sau 15 phút

---

## 🎉 Kết Quả

✅ Backend chạy 24/7 miễn phí  
✅ Frontend CDN cực nhanh  
✅ Database Supabase free 500MB  
✅ Tổng chi phí: **$0/tháng**

**QUAN TRỌNG**: Chỉ dùng 1 Web Service trên Render Free!
