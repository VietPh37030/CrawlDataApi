-- ============================================
-- SUPABASE SCHEMA FOR CRAWLER SERVICE
-- Run this SQL in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- STORIES TABLE (Novels)
-- ============================================
CREATE TABLE IF NOT EXISTS stories (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  author TEXT,
  description TEXT,
  genres TEXT[] DEFAULT '{}',
  status TEXT DEFAULT 'Đang ra',  -- 'Đang ra' hoặc 'Full'
  total_chapters INTEGER DEFAULT 0,
  cover_url TEXT,
  source_url TEXT,
  view_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_stories_slug ON stories(slug);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_updated ON stories(updated_at DESC);

-- Full text search for title and author
CREATE INDEX IF NOT EXISTS idx_stories_search ON stories USING GIN (to_tsvector('simple', title || ' ' || COALESCE(author, '')));

-- ============================================
-- CHAPTERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chapters (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  chapter_number INTEGER NOT NULL,
  title TEXT,
  content TEXT,  -- HTML or plain text content
  source_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Unique constraint: one chapter number per story
  CONSTRAINT unique_chapter_per_story UNIQUE (story_id, chapter_number)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_chapters_story ON chapters(story_id);
CREATE INDEX IF NOT EXISTS idx_chapters_story_number ON chapters(story_id, chapter_number);

-- ============================================
-- CRAWL TASKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_tasks (
  id TEXT PRIMARY KEY,  -- Using text ID like "task_abc123"
  story_url TEXT NOT NULL,
  status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
  progress INTEGER DEFAULT 0,
  message TEXT,
  error TEXT,
  novel_id UUID,  -- Reference to created story
  total_chapters INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON crawl_tasks(status);

-- ============================================
-- OPTIONAL: Auto-update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stories_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VERIFY TABLES CREATED
-- ============================================
SELECT 
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('stories', 'chapters', 'crawl_tasks');
