-- RESET DATABASE - Clear all data for fresh crawl
-- Run this in Supabase SQL Editor

-- Step 1: Clear all existing data
TRUNCATE TABLE chapters CASCADE;
TRUNCATE TABLE stories CASCADE;
TRUNCATE TABLE crawl_stats CASCADE;
TRUNCATE TABLE crawl_tasks CASCADE;

-- Step 2: Ensure unique constraints exist (required for upsert)
-- Drop old index if exists
DROP INDEX IF EXISTS idx_chapters_story_chapter;

-- Add constraint for chapters
ALTER TABLE chapters 
DROP CONSTRAINT IF EXISTS chapters_story_chapter_unique;

ALTER TABLE chapters 
ADD CONSTRAINT chapters_story_chapter_unique 
UNIQUE (story_id, chapter_number);

-- Add constraint for crawl_stats
ALTER TABLE crawl_stats 
DROP CONSTRAINT IF EXISTS crawl_stats_date_unique;

ALTER TABLE crawl_stats 
ADD CONSTRAINT crawl_stats_date_unique 
UNIQUE (date);

-- Step 3: Verify tables are empty
SELECT 'stories' as table_name, COUNT(*) as count FROM stories
UNION ALL
SELECT 'chapters', COUNT(*) FROM chapters
UNION ALL
SELECT 'crawl_stats', COUNT(*) FROM crawl_stats;

-- Step 4: Verify constraints exist
SELECT 
    tc.constraint_name, 
    tc.table_name
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'UNIQUE'
    AND tc.table_name IN ('chapters', 'crawl_stats');
