import logging
import google.generativeai as genai
import os
import asyncio

logger = logging.getLogger(__name__)

INVALID_OUTPUT_PATTERNS = {
    "please generate", "focus on the main ideas", "target length",
    "do not use markdown", "text to summarize", "based on the following text",
    "concise summary", "key points", "essential conclusions"
}

def is_invalid_output(text: str) -> bool:
    if not text or len(text.strip()) < 50:
        return True
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in INVALID_OUTPUT_PATTERNS)

def get_summary_prompt(text: str) -> str:
    word_count = len(text.split())
    target_length = max(5, min(3690, int(word_count * 0.36)))
    return f"""
Please generate a clear and concise summary of the following text.
Focus on the main ideas, key points, and essential conclusions.

Target length: {target_length} words.
Do not use markdown. Use plain text only.

Text to summarize:
{text.strip()}
"""

def _sync_summarize(prompt: str) -> str:
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini sync error: {e}")
        return None

async def generate_summary(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return "No content to summarize."

    prompt = get_summary_prompt(text)

    try:
        logger.info(f"Summarizing with Gemini 2.0 Flash...")
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_summarize, prompt),
            timeout=120.0
        )
        if result and not is_invalid_output(result):
            logger.info("✅ Success with Gemini 2.0 Flash")
            return result.strip()
    except Exception as e:
        logger.error(f"❌ Gemini failed: {e}")

    return "Summary could not be generated. Please try again later."