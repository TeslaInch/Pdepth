-- backend/caching_migration.sql
-- Run this script in your Supabase SQL Editor to apply caching changes to the live database.

ALTER TABLE public.pdf_documents 
ADD COLUMN IF NOT EXISTS file_hash TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS summary TEXT;

-- Create an index to quickly lookup PDFs by hash
CREATE INDEX IF NOT EXISTS idx_pdf_documents_file_hash ON public.pdf_documents(file_hash);
