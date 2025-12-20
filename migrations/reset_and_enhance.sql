-- =============================================
-- CRAWLER DATABASE RESET & ENHANCEMENT
-- Run this in Supabase SQL Editor
-- =============================================

-- 1. XÓA TOÀN BỘ DỮ LIỆU CŨ
TRUNCATE TABLE chapters CASCADE;
TRUNCATE TABLE stories CASCADE;
TRUNCATE TABLE crawl_tasks CASCADE;

-- 2. ĐẢM BẢO CỘT CONTENT TỒN TẠI TRONG CHAPTERS
ALTER TABLE chapters 
ADD COLUMN IF NOT EXISTS content TEXT DEFAULT '';

-- 3. THÊM INDEX CHO PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_chapters_story_id ON chapters(story_id);
CREATE INDEX IF NOT EXISTS idx_chapters_chapter_number ON chapters(chapter_number);
CREATE INDEX IF NOT EXISTS idx_stories_slug ON stories(slug);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);

-- 4. TẠO BẢNG GENRES (THỂ LOẠI)
CREATE TABLE IF NOT EXISTS genres (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    story_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. TẠO BẢNG LIÊN KẾT STORY-GENRE (NHIỀU-NHIỀU)
CREATE TABLE IF NOT EXISTS story_genres (
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    genre_id UUID REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (story_id, genre_id)
);

-- 6. TẠO BẢNG THỐNG KÊ CRAWL THEO NGÀY
CREATE TABLE IF NOT EXISTS crawl_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE UNIQUE NOT NULL DEFAULT CURRENT_DATE,
    stories_crawled INT DEFAULT 0,
    chapters_crawled INT DEFAULT 0,
    content_fetched INT DEFAULT 0,
    errors INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. TẠO BẢNG READING HISTORY (LỊCH SỬ ĐỌC - TÙY CHỌN)
CREATE TABLE IF NOT EXISTS reading_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),  -- Có thể là anonymous ID
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    read_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. INDEX CHO BẢNG MỚI
CREATE INDEX IF NOT EXISTS idx_story_genres_story ON story_genres(story_id);
CREATE INDEX IF NOT EXISTS idx_story_genres_genre ON story_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_crawl_stats_date ON crawl_stats(date);
CREATE INDEX IF NOT EXISTS idx_reading_history_story ON reading_history(story_id);

-- 9. FUNCTION CẬP NHẬT STORY_COUNT TRONG GENRES (TRIGGER)
CREATE OR REPLACE FUNCTION update_genre_story_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE genres SET story_count = story_count + 1 WHERE id = NEW.genre_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE genres SET story_count = story_count - 1 WHERE id = OLD.genre_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 10. TẠO TRIGGER
DROP TRIGGER IF EXISTS trigger_update_genre_count ON story_genres;
CREATE TRIGGER trigger_update_genre_count
AFTER INSERT OR DELETE ON story_genres
FOR EACH ROW EXECUTE FUNCTION update_genre_story_count();

-- DONE!
SELECT 'Database reset and enhanced successfully!' as message;
