import os
from supabase import create_client, Client
from config import Config

supabase_url = Config.SUPABASE_URL
supabase_key = Config.SUPABASE_KEY

if not supabase_url or not supabase_key:
    # Use a dummy client or raise during development if you want strict checking
    # raise ValueError("SUPABASE_URL and SUPABASE_KEY are missing from environment variables")
    supabase: Client = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)
