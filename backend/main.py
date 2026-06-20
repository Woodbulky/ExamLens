"""
ExamLens Backend — FastAPI Application Entry Point

AI-powered university exam analysis platform.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables at startup
REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
]

# GROQ_API_KEY is not validated at startup — only needed in Phase 4 (Analysis Pipeline)


for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(
            f"Missing required environment variable: {var}. "
            f"Copy .env.example to .env and fill in all values."
        )

# Create FastAPI app
app = FastAPI(
    title="ExamLens API",
    description="AI-powered university exam analysis platform",
    version="1.0.0",
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# Build allowed origins list
allowed_origins = [
    frontend_url,
    "http://localhost:5173",             # Local dev
    "http://localhost:5174",             # Local dev (alt port)
    "http://localhost:5175",             # Local dev (alt port)
    "https://examlens.vercel.app",       # Production
    "https://examlens-ruby.vercel.app",  # Production (actual)
]

# Log for debugging CORS issues in production
print(f"[CORS] FRONTEND_URL = {frontend_url}")
print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from routers.auth import router as auth_router
from routers.subjects import router as subjects_router
from routers.upload import router as upload_router
from routers.syllabus import router as syllabus_router
from routers.analysis import router as analysis_router
from routers.dashboard import router as dashboard_router
from routers.export import router as export_router
from routers.chat import router as chat_router
from routers.professor import router as professor_router

app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(upload_router)
app.include_router(syllabus_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)
app.include_router(export_router)
app.include_router(chat_router)
app.include_router(professor_router)


@app.get("/")
async def health_check():
    """Health check endpoint — verifies the API is running."""
    return {"status": "ExamLens API running"}
