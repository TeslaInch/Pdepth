---
trigger: always_on
---

These enforce your specific architecture:
markdown#

## Architecture
- Strictly follow layered architecture: Router → Service → Repository
- Routers handle HTTP only — no business logic in routers
- All business logic lives in the Service layer
- All database/external data access goes through Repository classes
- Never call the AI API directly from a router or repository

## Backend (Python / FastAPI)
- Use Pydantic models for ALL request and response schemas
- All endpoints must have response_model declared
- Use dependency injection via FastAPI Depends() for services and DB sessions
- Use async/await throughout — no blocking calls in async functions
- All AI API calls go through a dedicated AIService class in services/ai_service.py
- All YouTube API calls go through a dedicated YouTubeService class
- Use HTTPException with proper status codes — never return raw errors
- Group routes by feature: /videos, /summaries, /recommendations
- Use Alembic for all database migrations — never modify schema manually

## Frontend (TypeScript)
- Strict TypeScript — no `any` types allowed
- All API calls go through a central api/ module, never fetch directly in components
- Use custom hooks for all data fetching logic
- Define interfaces for every API response shape
- Separate concerns: components handle UI only, hooks handle data

## AI Integration
- Always chunk long transcripts before sending to AI API — max 4000 tokens per chunk
- Cache AI summaries — never re-summarize the same video ID twice
- Include retry logic with exponential backoff on all AI API calls
- Store raw transcript and generated summary separately in the database

## Testing
- Every service method must have a unit test
- Mock all external API calls (YouTube, AI) in tests — never hit real APIs in tests
- Use pytest with pytest-asyncio for async tests

## Git
- Never commit .env files
- Commit messages must follow: feat/fix/refactor/chore: description
```
