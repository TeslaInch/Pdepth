-- backend/pgvector_resize_migration.sql
-- WARNING: This will drop the existing pdf_chunks table and erase all existing vectors
-- Run this in your Supabase SQL Editor to resize the vector embeddings from 1536 (OpenAI) to 768 (Gemini).

DROP TABLE IF EXISTS public.pdf_chunks CASCADE;

CREATE TABLE public.pdf_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID NOT NULL REFERENCES public.pdf_documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Recreate index for semantic search (optional but recommended for speed)
CREATE INDEX ON public.pdf_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Recreate the match_chunks RPC function for the new 768 dimension
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  p_pdf_id uuid,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    pdf_chunks.id,
    pdf_chunks.content,
    1 - (pdf_chunks.embedding <=> query_embedding) AS similarity
  FROM pdf_chunks
  WHERE pdf_chunks.pdf_id = p_pdf_id
    AND pdf_chunks.user_id = p_user_id
    AND 1 - (pdf_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY pdf_chunks.embedding <=> query_embedding
  LIMIT match_count;
$$;
