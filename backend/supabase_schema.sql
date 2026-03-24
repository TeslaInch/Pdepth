-- Step 2: Supabase Schema Migration

-- 1. Create users table
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'paid')),
  stripe_customer_id TEXT,
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Create pdf_documents table
CREATE TABLE IF NOT EXISTS public.pdf_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pdf_documents ENABLE ROW LEVEL SECURITY;

-- 4. Create Policies for users
CREATE POLICY "Users can view own profile" 
ON public.users FOR SELECT 
USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
ON public.users FOR UPDATE 
USING (auth.uid() = id);

-- Note: User creation usually happens via a database trigger on auth.users creation, 
-- but if inserting manually from API, this policy allows it for the user:
CREATE POLICY "Users can insert own profile" 
ON public.users FOR INSERT 
WITH CHECK (auth.uid() = id);

-- 5. Create Policies for pdf_documents
CREATE POLICY "Users can view own pdfs" 
ON public.pdf_documents FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own pdfs" 
ON public.pdf_documents FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own pdfs" 
ON public.pdf_documents FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own pdfs" 
ON public.pdf_documents FOR DELETE 
USING (auth.uid() = user_id);
