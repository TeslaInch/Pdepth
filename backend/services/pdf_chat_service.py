import os
import re
from openai import AsyncOpenAI
from supabase_client import supabase

# Uses OPENAI_API_KEY from environment variables automatically
client = AsyncOpenAI() 

def chunk_text(text: str, max_words: int = 500) -> list[str]:
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_len + word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_len = word_count
        else:
            current_chunk.append(sentence)
            current_len += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

async def process_and_store_pdf_chunks(text: str, pdf_id: str, user_id: str):
    """
    Chunks the given text, fetches OpenAI embeddings, 
    and inserts the chunks into Supabase pgvector table.
    """
    chunks = chunk_text(text, max_words=300)
    if not chunks:
        return
        
    # Get embeddings for all chunks in batch
    response = await client.embeddings.create(
        input=chunks,
        model="text-embedding-ada-002"
    )
    
    records = []
    for i, chunk_text_content in enumerate(chunks):
        embedding = response.data[i].embedding
        records.append({
            "pdf_id": pdf_id,
            "user_id": user_id,
            "content": chunk_text_content,
            "embedding": embedding
        })
        
    if records:
        # Supabase Python SDK can handle batch inserts
        supabase.table("pdf_chunks").insert(records).execute()

async def generate_chat_answer(pdf_id: str, user_id: str, question: str) -> str:
    """
    1. Embeds the user question.
    2. Runs RPC match_chunks to semantic search the pdf.
    3. Feeds fetched chunks to the LLM to get the answer.
    """
    # 1. Embed the question
    q_response = await client.embeddings.create(
        input=question,
        model="text-embedding-ada-002"
    )
    query_embedding = q_response.data[0].embedding
    
    # 2. Match chunks via RPC
    rpc_params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.70,
        "match_count": 5,
        "p_pdf_id": pdf_id,
        "p_user_id": user_id
    }
    match_response = supabase.rpc("match_chunks", rpc_params).execute()
    
    if not match_response.data:
        return "I could not find any relevant information in the document to answer your question."
        
    # 3. Formulate Context
    context = "\n\n".join([chunk["content"] for chunk in match_response.data])
    
    system_prompt = "You are a helpful assistant answering a question based ONLY on the provided document context."
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
    
    # 4. Generate Answer via OpenAI Model
    chat_response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )
    
    return chat_response.choices[0].message.content
