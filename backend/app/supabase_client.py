import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

if not supabase_url:
    raise RuntimeError("SUPABASE_URL is not set")

if not supabase_key:
    raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is not set")

supabase: Client = create_client(supabase_url, supabase_key)