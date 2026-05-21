"""
Conexión a Supabase via REST API (httpx)
Funciona en Render free tier sin restricciones de red TCP
"""

import os
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL")        # https://iadrtpohldpwaxlacfaz.supabase.co
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")        # anon key o service_role key

_client: httpx.AsyncClient | None = None


async def init_db():
    global _client
    _client = httpx.AsyncClient(
        base_url=f"{SUPABASE_URL}/rest/v1",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        timeout=10.0,
    )


async def get_db() -> httpx.AsyncClient:
    return _client


async def close_db():
    if _client:
        await _client.aclose()

