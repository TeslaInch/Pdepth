# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import os
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.pdf_utils import extract_text_from_pdf
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import recommend_videos_from_summary
from typing import Dict, List, Any, Optional
import time
import logging
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from llm.fallback import generate_summary as llm_generate_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# -----------------------------
# Auth & Plan Gating
# -----------------------------
from dependencies import get_current_user
from services.plan_gate_service import assert_feature_access
from repositories.pdf_repository import save_pdf_record
from supabase_client import supabase
from services.pdf_chat_service import process_and_store_pdf_chunks, generate_chat_answer

# -----------------------------
# Lifespan
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PDF Processing API...")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="PDF Processing API", lifespan=lifespan)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://pdepth.xyz",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "https://www.pdepth.xyz",
        "https://pdepth.vercel.app",
        "https://www.pdepth.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# -----------------------------
# Models
# -----------------------------
class ChatRequest(BaseModel):
    pdf_id: str
    question: str
class SummarizeRequest(BaseModel):
    text: str

class SummaryRequest(BaseModel):
    summary: str

class ProcessingResponse(BaseModel):
    message: str
    filename: str
    summary: str
    videos: List[Dict[str, Any]]
    status: str
    upload_date: str

# -----------------------------
# Smart Chunking
# -----------------------------
def smart_chunk_text(text: str, max_words: int = 3000) -> List[str]:
    import re
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

async def generate_summary_from_text(text: str) -> str:
    if not text.strip():
        return "No content to summarize."

    word_count = len(text.split())
    if word_count < 600:
        prompt = get_summary_prompt(text)
        return await llm_generate_summary(prompt)

    chunks = smart_chunk_text(text, 3000)
    tasks = [llm_generate_summary(get_summary_prompt(chunk)) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    summaries = [r for r in results if isinstance(r, str) and len(r.strip()) > 20]
    if not summaries:
        return "No valid summary could be generated."

    combined = "\n\n---\n\n".join(summaries)
    final_prompt = get_summary_prompt(combined)
    final = await llm_generate_summary(final_prompt)
    return final or "Summary could not be finalized."

def get_summary_prompt(text: str) -> str:
    word_count = len(text.split())
    target_length = max(5, min(36900, int(word_count * 0.20)))
    return f"""
Please generate a clear and concise summary of the following text.
Focus on the main ideas, key points, and essential conclusions.

Target length: {target_length} words.
Do not use markdown. Use plain text only.

Text to summarize:
{text.strip()}
"""

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {"message": "PDF Processing API", "version": "1.0.0"}


@app.post("/upload-pdf", response_model=ProcessingResponse)
@limiter.limit("5/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    user_id = user["id"]
    client_ip = request.client.host
    logger.info(f"📥 Upload initiated by user {user_id} from {client_ip}")

    # Enforce plan gating
    try:
        assert_feature_access(user, "max_pdfs")
    except HTTPException as e:
        logger.warning(f"🚨 Plan limit exceeded for user {user_id}: {e.detail}")
        raise e

    try:
        # Read file
        logger.info(f"📄 Reading file: '{file.filename}' ({file.size} bytes)")
        content = await file.read()

        # File size check
        if len(content) > 15 * 1024 * 1024:
            logger.warning(f"❌ File too large: {len(content)} bytes from {client_ip}")
            return JSONResponse(
                {"error": "File too large", "status": "too_large"},
                status_code=413
            )

        # PDF header check
        if not content.startswith(b"%PDF"):
            logger.warning(f"❌ Invalid PDF header from {client_ip}. First bytes: {content[:10]}")
            return JSONResponse(
                {"error": "Invalid PDF", "status": "invalid_pdf"},
                status_code=400
            )

        # Extract text
        logger.info("🔍 Starting text extraction...")
        text = extract_text_from_pdf(content)
        logger.info(f"📝 Text extracted. Length: {len(text)}, Preview: '{text[:200]}...'")

        REJECTION_INDICATORS = {
            "Could not extract text from PDF. The file may be corrupted or encrypted.",
            "Scanned PDFs are not supported. Please upload a text-based PDF.",
            "Empty PDF: No pages found."
        }

        # Check if the returned text is a rejection message (short and matches known patterns)
        if any(indicator in text.lower() for indicator in REJECTION_INDICATORS):
            # ✅ Log the full text preview, but return a clean, safe error
            logger.warning(f"🚫 Rejected content: '{text[:100]}...'")
            return JSONResponse(
                {
                    "error": text.strip(),  # Still send the message, but it's now short
                    "status": "invalid_content"
                },
                status_code=422
            )

        # Generate summary
        logger.info("🧠 Starting summarization pipeline...")
        summary = await generate_summary_from_text(text)
        logger.info(f"✅ Summary generated. Length: {len(summary)}")

        # Get videos
        if "could not generate summary" in summary.lower() or len(summary) < 100:
            videos = []
            logger.info("ℹ️ Skipping video recommendations due to poor summary.")
        else:
            try:
                videos = recommend_videos_from_summary(summary)
                logger.info(f"🎥 Found {len(videos)} video recommendations")
            except Exception as e:
                logger.warning(f"📹 Video recommendation failed: {e}")
                videos = []

        # Success: Save PDF document record to Supabase
        save_pdf_record(user_id=user["id"], file_name=file.filename, storage_path=f"{user['id']}/{file.filename}")
        logger.info("🎉 Upload completed successfully")

        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "summary": summary,
            "videos": videos,
            "status": "completed",
            "upload_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        # This will now catch and log the *exact* error
        logger.error(f"💥 CRITICAL: Upload failed with error: {type(e).__name__}: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": "Processing failed. Please try again.", "status": "error"},
            status_code=500
        )

@app.post("/upload-pdfs")
@limiter.limit("5/minute")
async def upload_multiple_pdfs(request: Request, files: List[UploadFile] = File(...), user: dict = Depends(get_current_user)):
    user_id = user["id"]
    client_ip = request.client.host
    logger.info(f"📥 Multi-Upload initiated by user {user_id} with {len(files)} files")

    results = []
    for file in files:
        # Enforce plan gating per upload
        try:
            assert_feature_access(user, "max_pdfs")
        except HTTPException as e:
            logger.warning(f"🚨 Plan limit exceeded for user {user_id}: {e.detail}")
            results.append({"filename": file.filename, "status": "failed", "error": "Plan limit exceeded"})
            continue

        try:
            content = await file.read()
            
            # File size check
            if len(content) > 15 * 1024 * 1024:
                results.append({"filename": file.filename, "status": "failed", "error": "File too large"})
                continue
                
            # PDF header check    
            if not content.startswith(b"%PDF"):
                results.append({"filename": file.filename, "status": "failed", "error": "Invalid PDF"})
                continue

            # Upload physically to Supabase Storage bucket
            storage_path = f"{user_id}/{file.filename}"
            supabase.storage.from_("pdfs").upload(
                path=storage_path, 
                file=content, 
                file_options={"content-type": "application/pdf"}
            )

            # Save metadata via repository
            pdf_record = save_pdf_record(user_id=user_id, file_name=file.filename, storage_path=storage_path)

            # Process chunks for Chat Support
            if pdf_record and "id" in pdf_record:
                await process_and_store_pdf_chunks(text, pdf_record["id"], user_id)

            results.append({
                "filename": file.filename,
                "status": "completed",
                "storage_path": storage_path,
                "message": "File uploaded and saved to Supabase successfully."
            })

        except Exception as e:
            logger.error(f"Failed processing {file.filename}: {str(e)}")
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return {"status": "completed", "total_processed": len(results), "results": results}

@app.post("/chat-pdf")
@limiter.limit("10/minute")
async def chat_pdf(request: Request, payload: ChatRequest, user: dict = Depends(get_current_user)):
    try:
        answer = await generate_chat_answer(
            pdf_id=payload.pdf_id, 
            user_id=user["id"], 
            question=payload.question
        )
        return {"answer": answer, "status": "completed"}
    except Exception as e:
        logger.error(f"Chat PDF error: {str(e)}", exc_info=True)
        return JSONResponse({"error": "Failed to process chat query"}, status_code=500)

@app.post("/summarize")
@limiter.limit("10/minute")
async def summarize_text(request: Request, payload: SummarizeRequest, user: dict = Depends(get_current_user)):
    try:
        text = payload.text.strip()
        if not text:
            return JSONResponse({"error": "No text provided"}, status_code=400)
        summary = await generate_summary_from_text(text)
        return {"summary": summary, "status": "completed"}
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return JSONResponse(
            {"error": "Failed to summarize text."}, status_code=500
        )

@app.post("/recommend-videos")
@limiter.limit("6/minute")
async def recommend_videos(request: Request, data: SummaryRequest):
    try:
        recommendations = recommend_videos_from_summary(data.summary)
        return {"success": True, "data": recommendations, "count": len(recommendations)}
    except Exception as e:
        logger.error(f"Video recommendation failed: {e}")
        return {"success": False, "error": "Could not fetch videos."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/auth/google")
async def auth_google(redirect_url: str = "http://pdepth.xyz/auth/callback"):
    try:
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_url}
        })
        return {"url": res.url}
    except Exception as e:
        logger.error(f"OAuth URL generation failed: {e}")
        return JSONResponse({"error": "Failed to generate OAuth URL"}, status_code=500)

@app.get("/auth/callback")
async def auth_callback(code: str):
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user_id": res.user.id,
            "email": res.user.email
        }
    except Exception as e:
        logger.error(f"OAuth Callback failed: {e}")
        return JSONResponse({"error": "Failed to exchange code for session"}, status_code=500)

from services.stripe_service import create_checkout_session, handle_webhook

@app.post("/payments/create-checkout")
async def create_checkout(user: dict = Depends(get_current_user)):
    try:
        url = create_checkout_session(user)
        return {"url": url}
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        return JSONResponse({"error": "Failed to create checkout session"}, status_code=500)

@app.post("/payments/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        return JSONResponse({"error": "Missing signature"}, status_code=400)
        
    try:
        handle_webhook(payload, sig_header)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Stripe Webhook Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)