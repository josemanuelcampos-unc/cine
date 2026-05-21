"""
Conexión a Supabase (PostgreSQL) via asyncpg
"""
 
import os
import asyncpg
from typing import AsyncGenerator
 
DATABASE_URL = os.environ.get("DATABASE_URL")
 
_pool: asyncpg.Pool | None = None
 
 
async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
    )
 
 
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    async with _pool.acquire() as conn:
        yield conn
 

