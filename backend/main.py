# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.pdf_utils import extract_text_from_file
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import recommend_videos_from_summary
from typing import Dict, List, Any
import time
import logging
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
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
from repositories.pdf_repository import save_pdf_record, find_pdf_by_hash
from supabase_client import supabase
import hashlib
from services.pdf_chat_service import process_and_store_pdf_chunks, generate_chat_answer
from services.question_service import generate_questions

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

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Please wait a moment and try again."}
    )

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

    # Send the payload exclusively as a single-shot execution avoiding arbitrary stacking
    prompt = get_summary_prompt(text)
    return await llm_generate_summary(prompt)

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
        assert_feature_access(user, "uploads_per_hour")
    except HTTPException as e:
        if e.status_code == 429 and isinstance(e.detail, dict) and e.detail.get("error") == "limit_reached":
            logger.warning(f"🚨 Time limit reached for user {user_id}: {e.detail}")
            return JSONResponse(e.detail, status_code=429)
            
        # Instead of 'raise e' leaking 500 error stack traces onto the native frontend
        logger.error(f"💥 Native Access Error: {getattr(e, 'detail', str(e))}")
        return JSONResponse(
            {"error": "Something went wrong on our end. Please try again shortly.", "status": "error"},
            status_code=500
        )

    try:
        # Read file
        logger.info(f"📄 Reading file: '{file.filename}' ({file.size} bytes)")
        content = await file.read()

        # File size check
        if len(content) > 15 * 1024 * 1024:
            logger.warning(f"❌ File too large: {len(content)} bytes from {client_ip}")
            return JSONResponse(
                {"error": "This file exceeds the allowed size limit. Please upload a smaller file.", "status": "too_large"},
                status_code=413
            )

        # File type check
        ext = file.filename.lower().split('.')[-1]
        valid_exts = ['pdf', 'txt', 'md', 'docx']
        if ext not in valid_exts:
            logger.warning(f"❌ Unsupported file type from {client_ip}: {file.filename}")
            return JSONResponse({"error": "This file type is not supported. Please upload a PDF, TXT, DOCX, or MD file.", "status": "invalid_file"}, status_code=400)
            
        # PDF specific header check
        if ext == 'pdf' and not content.startswith(b"%PDF"):
            logger.warning(f"❌ Invalid PDF header from {client_ip}. First bytes: {content[:10]}")
            return JSONResponse(
                {"error": "This file type is not supported. Please upload a PDF, TXT, DOCX, or MD file.", "status": "invalid_pdf"},
                status_code=400
            )

        # File Hash Cache Check
        file_hash = hashlib.sha256(content).hexdigest()
        cached_pdf = find_pdf_by_hash(file_hash)

        if cached_pdf and cached_pdf.get("summary"):
            logger.info(f"⚡ Cache hit for {file.filename}! Skipping AI processing.")
            summary = cached_pdf["summary"]
            
            videos = []
            if len(summary) > 100 and "could not generate summary" not in summary.lower():
                try:
                    videos = recommend_videos_from_summary(summary)
                except Exception as e:
                    logger.warning(f"📹 Video recommendation failed on cache hit: {e}")

            # Ensure we still save the file record for this specific user's dashboard!
            save_pdf_record(user_id=user["id"], file_name=file.filename, storage_path=f"{user['id']}/{file.filename}", file_hash=file_hash, summary=summary)

            return {
                "message": "PDF processed successfully (Cache Hit)",
                "filename": file.filename,
                "summary": summary,
                "videos": videos,
                "status": "completed",
                "upload_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        # Extract text (Cache Miss)
        logger.info("🔍 Starting text extraction...")
        text = extract_text_from_file(content, file.filename)
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
                    "error": "We couldn't read this file. It may be corrupted or in an unsupported format. Try re-exporting or converting it.",
                    "status": "invalid_content"
                },
                status_code=422
            )

        # Generate summary
        logger.info("🧠 Starting summarization pipeline...")
        summary = await generate_summary_from_text(text)
        logger.info(f"✅ Summary generated. Length: {len(summary)}")

        # Get videos
        videos = []
        summary_low = summary.lower()
        if "could not be generated" in summary_low or "could not generate summary" in summary_low or len(summary) < 50:
            logger.warning(f"🚫 AI Summary failure - aborting DB hook entirely.")
            # We strictly bypass save_pdf_record preventing Limit consumption natively!
            return JSONResponse(
                {"error": "Failed to generate AI summary. The document may be too complex or the AI service timed out.", "status": "ai_failure"},
                status_code=422
            )
        else:
            try:
                videos = recommend_videos_from_summary(summary)
                logger.info(f"🎥 Found {len(videos)} video recommendations")
            except Exception as e:
                logger.warning(f"📹 Video recommendation failed: {e}")

        # Success: Upload physical bytes and Save PDF document exclusively upon perfect generation
        storage_path = f"{user['id']}/{file.filename}"
        try:
            supabase.storage.from_("pdfs").upload(path=storage_path, file=content, file_options={"content-type": "application/pdf"})
        except Exception as e:
            logger.warning(f"File already existed in storage natively or bucket error: {e}")
            
        pdf_record = save_pdf_record(user_id=user["id"], file_name=file.filename, storage_path=storage_path, file_hash=file_hash, summary=summary)
        logger.info("🎉 Upload completed successfully")

        # Vectorize chunks for Chat support
        if pdf_record and pdf_record.get("id"):
            try:
                await process_and_store_pdf_chunks(text, pdf_record["id"], user["id"])
                logger.info(f"🔗 Chunks vectorized for pdf_id={pdf_record['id']}")
            except Exception as e:
                logger.warning(f"⚠️ Chunk vectorization failed (non-blocking): {e}")

        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "summary": summary,
            "videos": videos,
            "status": "completed",
            "upload_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_id": pdf_record.get("id", "") if pdf_record else ""
        }

    except Exception as e:
        # This will now catch and log the *exact* error
        logger.error(f"💥 CRITICAL: Upload failed with error: {type(e).__name__}: {str(e)}", exc_info=True)
        err_msg = str(e).lower()
        if any(phrase in err_msg for phrase in ["timeout", "quota", "rate limit", "api", "gemini", "groq", "unauthorized", "connection", "remote"]):
            safe_msg = "Our AI service is temporarily unavailable. Please try again in a few minutes."
        else:
            safe_msg = "Something went wrong on our end. Please try again shortly."
            
        return JSONResponse(
            {"error": safe_msg, "status": "error"},
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
            assert_feature_access(user, "uploads_per_hour")
        except HTTPException as e:
            if e.status_code == 429 and isinstance(e.detail, dict) and e.detail.get("error") == "limit_reached":
                logger.warning(f"🚨 Time limit reached for user {user_id}: {e.detail}")
                results.append({
                    "filename": file.filename, 
                    "status": "failed", 
                    "error": e.detail.get("message"), 
                    "limit_reached": True, 
                    "retry_time": e.detail.get("retry_time")
                })
            else:
                logger.warning(f"🚨 General gating error for user {user_id}: {e.detail}")
                results.append({"filename": file.filename, "status": "failed", "error": f"{e.detail}"})
            continue

        try:
            content = await file.read()
            
            # File size check
            if len(content) > 15 * 1024 * 1024:
                results.append({"filename": file.filename, "status": "failed", "error": "This file exceeds the allowed size limit. Please upload a smaller file."})
                continue
                
            # File type check
            ext = file.filename.lower().split('.')[-1]
            valid_exts = ['pdf', 'txt', 'md', 'docx']
            if ext not in valid_exts:
                results.append({"filename": file.filename, "status": "failed", "error": "This file type is not supported. Please upload a PDF, TXT, DOCX, or MD file."})
                continue
                
            # PDF header check    
            if ext == 'pdf' and not content.startswith(b"%PDF"):
                results.append({"filename": file.filename, "status": "failed", "error": "This file type is not supported. Please upload a PDF, TXT, DOCX, or MD file."})
                continue

            # Generate summary natively
            summary = await generate_summary_from_text(text)
            
            # AI Inference Checkpoint Validation
            summary_low = summary.lower()
            if "could not be generated" in summary_low or "could not generate summary" in summary_low or len(summary) < 50:
                logger.warning(f"🚫 AI Summary generated fallback - avoiding limit bump.")
                results.append({"filename": file.filename, "status": "failed", "error": "AI could not generate a summary."})
                continue

            # Upload physically to Supabase Storage bucket
            storage_path = f"{user_id}/{file.filename}"
            try:
                supabase.storage.from_("pdfs").upload(
                    path=storage_path, 
                    file=content, 
                    file_options={"content-type": "application/pdf"}
                )
            except Exception as e:
                pass # Usually implies existing record collision safely

            # Save metadata via repository
            pdf_record = save_pdf_record(user_id=user_id, file_name=file.filename, storage_path=storage_path, file_hash=file_hash, summary=summary)

            # Process chunks for Chat Support
            if pdf_record and "id" in pdf_record:
                if len(text) > 100 and "scanned pdfs are not supported" not in text.lower():
                    await process_and_store_pdf_chunks(text, pdf_record["id"], user_id)

            results.append({
                "filename": file.filename,
                "status": "completed",
                "storage_path": storage_path,
                "message": "File uploaded and saved to Supabase successfully."
            })

        except Exception as e:
            logger.error(f"💥 CRITICAL: Failed processing {file.filename}: {str(e)}", exc_info=True)
            err_msg = str(e).lower()
            if any(phrase in err_msg for phrase in ["timeout", "quota", "rate limit", "api", "gemini", "groq", "unauthorized", "connection", "remote"]):
                safe_msg = "Our AI service is temporarily unavailable. Please try again in a few minutes."
            else:
                safe_msg = "Something went wrong on our end. Please try again shortly."
            raise HTTPException(status_code=500, detail=safe_msg)

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

class RetryRequest(BaseModel):
    pdf_id: str

@app.post("/retry-summary")
@limiter.limit("5/minute")
async def retry_summary(request: Request, payload: RetryRequest, user: dict = Depends(get_current_user)):
    try:
        # Secure database fetch
        res = supabase.table("pdf_documents").select("*").eq("id", payload.pdf_id).eq("user_id", user["id"]).execute()
        if not res.data:
            return JSONResponse({"error": "Document not found or unauthorized"}, status_code=404)
        
        doc = res.data[0]
        storage_path = doc.get("storage_path")
        if not storage_path:
            return JSONResponse({"error": "Original file not found in storage buckets"}, status_code=404)
            
        # Download strictly from Supabase Bucket seamlessly 
        file_bytes = supabase.storage.from_("pdfs").download(storage_path)
        text = extract_text_from_file(file_bytes, doc.get("file_name", "document.pdf"))
        
        # Validates corrupted states heavily
        REJECTION_INDICATORS = {
            "could not extract text",
            "scanned pdfs are not supported",
            "empty pdf"
        }
        if any(ind in text.lower() for ind in REJECTION_INDICATORS):
            return JSONResponse({"error": "We couldn't read this file. It may be corrupted or in an unsupported format."}, status_code=422)

        # Triggers pure UI-gating prompt logic via fallback routers
        summary = await generate_summary_from_text(text)
        if "could not generate summary" in summary.lower() or len(summary) < 50:
            return JSONResponse({"error": "Failed to generate AI summary."}, status_code=422)
            
        supabase.table("pdf_documents").update({"summary": summary}).eq("id", payload.pdf_id).execute()
        
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Retry Generation failed: {e}")
        err_msg = str(e).lower()
        if any(p in err_msg for p in ["timeout", "quota", "rate limit", "api", "gemini", "groq", "unauthorized"]):
            safe_msg = "Our AI service is temporarily unavailable. Please try again in a few minutes."
        else:
            safe_msg = "Something went wrong on our end. Please try again shortly."
        return JSONResponse({"error": safe_msg, "status": "error"}, status_code=500)

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

# -----------------------------
# Question Generation
# -----------------------------
class QuestionRequest(BaseModel):
    """Request schema for question generation."""
    text: str
    question_type: str = "mcq"  # 'mcq', 'essay', or 'both'
    difficulty: str = "medium"  # 'easy', 'medium', 'hard'
    count: int = 5

@app.post("/generate-questions")
@limiter.limit("5/minute")
async def generate_questions_endpoint(
    request: Request,
    data: QuestionRequest,
    user: dict = Depends(get_current_user)
):
    """Generate MCQ and/or essay questions from document text."""
    # Plan gating
    if data.question_type in ("essay", "both"):
        try:
            assert_feature_access(user, "essay_questions")
        except HTTPException as e:
            logger.warning(f"Essay access denied for user {user['id']}")
            raise e

    try:
        result = await generate_questions(
            text=data.text,
            question_type=data.question_type,
            difficulty=data.difficulty,
            count=data.count,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        return JSONResponse({"error": "Failed to generate questions."}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}



from services.paystack_service import initialize_transaction, handle_webhook, verify_paystack_transaction

@app.post("/payments/create-checkout")
async def create_checkout(user: dict = Depends(get_current_user)):
    try:
        url = await initialize_transaction(user)
        return {"url": url}
    except Exception as e:
        logger.error(f"Checkout initialization error: {e}")
        return JSONResponse({"error": "Failed to create Paystack checkout"}, status_code=500)

@app.get("/payments/verify")
async def verify_payment(reference: str, user: dict = Depends(get_current_user)):
    """Active server-side verification of payment status"""
    try:
        success = await verify_paystack_transaction(reference=reference, user_id=user["id"])
        if success:
            return {"status": "success", "message": "Subscription upgraded perfectly."}
        else:
            return JSONResponse({"error": "Transaction verification failed or pending."}, status_code=400)
    except Exception as e:
        logger.error(f"Explicit verification error: {e}")
        return JSONResponse({"error": "Failed to explicitly verify payment."}, status_code=500)

@app.post("/payments/webhook")
async def paystack_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("x-paystack-signature")
    
    if not sig_header:
        return JSONResponse({"error": "Missing Paystack signature"}, status_code=400)
        
    try:
        success = handle_webhook(payload, sig_header)
        if success:
            return {"status": "success"}
        return JSONResponse({"error": "Unhandled event"}, status_code=400)
    except Exception as e:
        logger.error(f"Paystack Webhook Error: {e}")
        return JSONResponse({"error": "Webhook processing failed"}, status_code=400)