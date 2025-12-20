-- Migration: Add unique constraint to crawl_stats.date for upsert to work properly
-- This allows the backend to update_crawl_stats() using upsert on date column

-- Add unique constraint if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'crawl_stats_date_key'
    ) THEN
        ALTER TABLE crawl_stats ADD CONSTRAINT crawl_stats_date_key UNIQUE (date);
    END IF;
END $$;

-- Insert initial stats for today if empty (to test the chart)
INSERT INTO crawl_stats (date, stories_crawled, chapters_crawled, content_fetched, errors)
VALUES (CURRENT_DATE, 0, 0, 0, 0)
ON CONFLICT (date) DO NOTHING;
