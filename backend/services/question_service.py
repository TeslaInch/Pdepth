import os
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

async def generate_questions(
    text: str,
    question_type: str = "mcq",
    difficulty: str = "medium",
    count: int = 5,
) -> dict:
    """
    Generate MCQ, Essay, or both question types from document text using Groq LLM.

    Args:
        text: The source document text to generate questions from.
        question_type: 'mcq', 'essay', or 'both'.
        difficulty: 'easy', 'medium', or 'hard'.
        count: Number of questions to generate per type.

    Returns:
        Dictionary with 'mcq' and/or 'essay' keys containing generated questions.
    """
    if not text or len(text.strip()) < 50:
        return {"error": "Text is too short to generate meaningful questions."}

    groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    # Truncate text to avoid exceeding context limits
    max_chars = 12000
    truncated_text = text[:max_chars] if len(text) > max_chars else text

    results = {}

    if question_type in ("mcq", "both"):
        mcq_prompt = f"""Based on the following text, generate {count} multiple-choice questions at a {difficulty} difficulty level.

Rules:
- Each question must have exactly 4 options labeled A, B, C, D
- Exactly one option must be the correct answer
- Questions should test understanding, not just recall
- For 'easy': focus on basic facts and definitions
- For 'medium': focus on understanding and application
- For 'hard': focus on analysis, evaluation, and inference

Format your response EXACTLY as a JSON array like this (no markdown, no extra text):
[
  {{
    "question": "What is...?",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "explanation": "Brief explanation of why A is correct."
  }}
]

Text:
{truncated_text}"""

        try:
            mcq_response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert academic question generator. Output only valid JSON arrays. No markdown."},
                    {"role": "user", "content": mcq_prompt}
                ],
                temperature=0.4,
            )
            raw = mcq_response.choices[0].message.content.strip()
            # Try to parse JSON
            import json
            # Strip potential markdown code fences
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results["mcq"] = json.loads(raw)
        except Exception as e:
            logger.error(f"MCQ generation failed: {e}")
            results["mcq"] = []

    if question_type in ("essay", "both"):
        essay_prompt = f"""Based on the following text, generate {count} essay/open-ended questions at a {difficulty} difficulty level.

Rules:
- Questions should encourage critical thinking and detailed responses
- For 'easy': basic comprehension and summary questions
- For 'medium': analysis and comparison questions
- For 'hard': evaluation, synthesis, and argumentation questions
- Include a brief model answer outline for each

Format your response EXACTLY as a JSON array like this (no markdown, no extra text):
[
  {{
    "question": "Discuss the...",
    "suggested_answer": "A good answer would cover..."
  }}
]

Text:
{truncated_text}"""

        try:
            essay_response = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert academic question generator. Output only valid JSON arrays. No markdown."},
                    {"role": "user", "content": essay_prompt}
                ],
                temperature=0.5,
            )
            raw = essay_response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            import json
            results["essay"] = json.loads(raw)
        except Exception as e:
            logger.error(f"Essay generation failed: {e}")
            results["essay"] = []

    return results
