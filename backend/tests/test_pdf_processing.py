import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Set dummy env vars to prevent global module instantiation crashes
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["GROQ_API_KEY"] = "dummy"
os.environ["GEMINI_API_KEY"] = "dummy"

# Import the functions we want to test
from utils.pdf_utils import extract_text_from_pdf
from main import upload_multiple_pdfs, upload_pdf
from fastapi import Request, UploadFile

@patch("utils.pdf_utils.fitz.open")
@patch("utils.pdf_utils.extract_text_via_gemini_vision")
def test_extract_text_fallback_on_empty(mock_gemini, mock_fitz):
    # Setup mock PyMuPDF to return empty pages (triggering < 50 chars fallback)
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "   " # small text
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz.return_value.__enter__.return_value = mock_doc

    mock_gemini.return_value = "Simulated OCR Text from Gemini"

    result = extract_text_from_pdf(b"fake_pdf_bytes")
    
    # Assert it called Gemini fallback
    mock_gemini.assert_called_once_with(b"fake_pdf_bytes")
    assert result == "Simulated OCR Text from Gemini"


@patch("utils.pdf_utils.fitz.open")
@patch("utils.pdf_utils.extract_text_via_gemini_vision")
def test_extract_text_fallback_on_scanner_watermarks(mock_gemini, mock_fitz):
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_page = MagicMock()
    # Scanned watermark text
    mock_page.get_text.return_value = "Scanned by CamScanner document"
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz.return_value.__enter__.return_value = mock_doc

    mock_gemini.return_value = "OCR Output"

    result = extract_text_from_pdf(b"fake_bytes")
    
    # Text length is small & watermark prominent -> should trigger Gemini OCR
    mock_gemini.assert_called_once()
    assert result == "OCR Output"


@pytest.mark.asyncio
@patch("main.extract_text_from_pdf")
@patch("main.process_and_store_pdf_chunks")
@patch("main.save_pdf_record")
@patch("main.supabase")
async def test_upload_multiple_pdfs(mock_supabase, mock_save_record, mock_process_chunks, mock_extract):
    # The extraction shouldn't crash with undefined 'text'
    mock_extract.return_value = "This is some extracted text for the chunker to process."
    mock_save_record.return_value = {"id": "test_pdf_id"}
    
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "127.0.0.1"

    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.size = 1000
    mock_file.read.return_value = b"%PDF-1.4\n...fake content..."
    
    mock_user = {"id": "user_123", "plan": "paid"} # bypassing limits

    with patch("main.assert_feature_access"):
        response = await upload_multiple_pdfs(mock_request, [mock_file], mock_user)
    
    assert response["status"] == "completed"
    assert response["total_processed"] == 1
    mock_extract.assert_called_once()
    mock_process_chunks.assert_awaited_once()


@pytest.mark.asyncio
@patch("main.find_pdf_by_hash")
@patch("main.extract_text_from_pdf")
async def test_upload_pdf_cache_hit(mock_extract, mock_find_hash):
    # Setup Cache Hit
    mock_find_hash.return_value = {
        "file_hash": "somehash", 
        "summary": "This was already summarized."
    }
    
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "127.0.0.1"

    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "cached.pdf"
    mock_file.size = 1000
    mock_file.read.return_value = b"%PDF-cache"

    mock_user = {"id": "user_123", "plan": "paid"}

    with patch("main.assert_feature_access"), \
         patch("main.save_pdf_record"), \
         patch("main.recommend_videos_from_summary") as mock_vids:
        
        mock_vids.return_value = [{"title": "Test Video"}]
        
        response = await upload_pdf(mock_request, mock_file, mock_user)
        
    # Assert cache skipped extraction entirely
    mock_extract.assert_not_called()
    assert response["status"] == "completed"
    assert "Cache Hit" in response["message"]
    assert response["summary"] == "This was already summarized."
