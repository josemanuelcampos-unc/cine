"""
Conexión a Supabase (PostgreSQL) via asyncpg
"""

import os
import asyncpg
from typing import AsyncGenerator

# Variable de entorno — se configura en Render
DATABASE_URL = os.environ.get("DATABASE_URL")
# Supabase usa SSL; asyncpg necesita ssl='require'


_pool: asyncpg.Pool | None = None


async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        ssl="require",
        min_size=1,
        max_size=10,
    )


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    async with _pool.acquire() as conn:
        yield conn
