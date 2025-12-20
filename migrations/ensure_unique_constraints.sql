-- Migration: Ensure proper unique constraint for chapters upsert
-- Run this in Supabase SQL Editor

-- First drop the index if it exists (indexes don't work with ON CONFLICT)
DROP INDEX IF EXISTS idx_chapters_story_chapter;

-- Add unique constraint on story_id + chapter_number
-- This is required for upsert ON CONFLICT to work properly
ALTER TABLE chapters 
DROP CONSTRAINT IF EXISTS chapters_story_chapter_unique;

ALTER TABLE chapters 
ADD CONSTRAINT chapters_story_chapter_unique 
UNIQUE (story_id, chapter_number);

-- Also ensure crawl_stats has unique on date
ALTER TABLE crawl_stats 
DROP CONSTRAINT IF EXISTS crawl_stats_date_unique;

ALTER TABLE crawl_stats 
ADD CONSTRAINT crawl_stats_date_unique 
UNIQUE (date);

-- Verify constraints were created
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'UNIQUE'
    AND tc.table_name IN ('chapters', 'crawl_stats');
