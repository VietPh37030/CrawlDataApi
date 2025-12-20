-- Migration: Add storage columns to chapters table
-- Run this in Supabase SQL Editor

-- Add storage_path column to store file path in Storage bucket
ALTER TABLE chapters 
ADD COLUMN IF NOT EXISTS storage_path TEXT;

-- Add is_archived flag to indicate content is saved in Storage
ALTER TABLE chapters 
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Create index for faster lookup of archived chapters
CREATE INDEX IF NOT EXISTS idx_chapters_is_archived 
ON chapters(is_archived) 
WHERE is_archived = TRUE;

-- Verify columns added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'chapters' 
AND column_name IN ('storage_path', 'is_archived');
