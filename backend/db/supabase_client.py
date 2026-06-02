"""
Supabase Client — Database and Storage access for ExamLens backend.

Uses the service role key for full access (bypasses RLS).
The backend is the only place where service role key is used.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file. "
        "Copy .env.example to .env and fill in the values."
    )

# Service role client — bypasses RLS for backend operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    """Get the Supabase client instance."""
    return supabase
