-- Step 7 Part 2: pgvector and chat with PDF schema

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create pdf_chunks table
CREATE TABLE IF NOT EXISTS public.pdf_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID NOT NULL REFERENCES public.pdf_documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536)
);

-- 3. Enable RLS
ALTER TABLE public.pdf_chunks ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies
CREATE POLICY "Users can view own pdf chunks" 
ON public.pdf_chunks FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own pdf chunks" 
ON public.pdf_chunks FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own pdf chunks" 
ON public.pdf_chunks FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own pdf chunks" 
ON public.pdf_chunks FOR DELETE 
USING (auth.uid() = user_id);

-- 5. Create match_chunks RPC
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT,
  p_pdf_id UUID,
  p_user_id UUID
)
RETURNS TABLE (
  id UUID,
  pdf_id UUID,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.pdf_id,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM pdf_chunks c
  WHERE c.pdf_id = p_pdf_id AND c.user_id = p_user_id
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
