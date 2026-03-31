# utils/youtube_utils.py
import httpx
import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# YouTube API Config
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not set in environment")

BASE_URL = "https://www.googleapis.com/youtube/v3/search"  # ✅ Fixed: no trailing spaces

# Stopwords for keyword extraction
STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with from
you your we our can could should would may might about over under between among across within without into onto than
i me my mine he she him her his hers its it's them they theirs us we ours who whom which what when where how why
pdf text page pages doc docs document study course topic lecture lesson exam exam(s) note notes
""".split())

def extract_keywords(text: str, k: int = 6) -> list:
    """
    Extract top k keywords using frequency, position, and context.
    Works well even when no word repeats (e.g., academic texts).
    """
    if not text or len(text.strip()) < 50:
        return []

    # Split into sentences and words
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    tokens = [w for w in words if w not in STOPWORDS and len(w) > 2]

    if not tokens:
        return []

    # Score each word
    scores = {}
    first_200 = text.lower()[:200]  # Words in intro are more important

    for word in set(tokens):
        score = 0

        # 1. Frequency
        freq = tokens.count(word)
        score += freq * 3

        # 2. Appears in first 200 chars?
        if word in first_200:
            score += 5

        # 3. Appears in multiple sentences?
        sentence_count = sum(1 for s in sentences if word in s.lower())
        score += sentence_count * 2

        # 4. Long or compound word? (e.g., dose-response, toxicology)
        if len(word) > 7 or '-' in word:
            score += 2

        # 5. Demote common verbs
        if word.endswith('ing') and word not in ['building', 'engineering', 'modeling', 'learning']:
            score *= 0.5

        scores[word] = score

    # Sort by score and return top k
    keywords = [word for word, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]]

    # Fallback
    if not keywords:
        return ["lecture", "introduction", "overview"]

    return keywords

def recommend_videos_from_summary(summary: str) -> List[Dict[str, Any]]:
    """
    Recommend YouTube videos using smart keyword extraction.
    Returns empty list if summary is invalid.
    """
    if not summary or len(summary.strip()) < 50:
        return []

    try:
        # Extract keywords
        keywords = extract_keywords(summary, k=6)

        # Build query: use keywords, but ensure it's meaningful
        if keywords:
            query = " ".join(keywords)
        else:
            query = "lecture introduction overview"

        search_query = f"{query} tutorial"

        # YouTube API request
        params = {
            "part": "snippet",
            "q": search_query,
            "key": API_KEY,
            "maxResults": 6,
            "type": "video",
            "order": "relevance"
        }

        response = httpx.get(BASE_URL, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()

        videos = []
        seen_video_ids = set()

        for item in data.get("items", []):
            try:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                title = snippet.get("title", "")
                channel = snippet.get("channelTitle", "")

                if not title or not channel or video_id in seen_video_ids:
                    continue

                videos.append({
                    "id": video_id,
                    "title": title,
                    "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url",
                        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
                    "duration": "Unknown",
                    "publishedAt": snippet.get("publishedAt", ""),
                })
                seen_video_ids.add(video_id)
            except Exception as e:
                print(f"Error parsing video: {e}")
                continue

        return videos[:6]

    except Exception as e:
        print(f"YouTube search failed: {e}")
        return []