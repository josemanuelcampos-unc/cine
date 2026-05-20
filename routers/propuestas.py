"""
Router de propuestas curriculares
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncpg

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────

class PropuestaCreate(BaseModel):
    titulo: str
    texto_fuente: Optional[str] = None
    unidad_academica: Optional[str] = None


class PropuestaOut(BaseModel):
    id: str
    titulo: str
    texto_fuente: Optional[str]
    unidad_academica: Optional[str]
    creado_en: str


# ── Endpoints ──────────────────────────────────────────────

@router.post("/", response_model=PropuestaOut, status_code=201)
async def crear_propuesta(
    data: PropuestaCreate,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    row = await db.fetchrow(
        """INSERT INTO propuestas (titulo, texto_fuente, unidad_academica, creado_por)
           VALUES ($1, $2, $3, $4::uuid)
           RETURNING id::text, titulo, texto_fuente, unidad_academica,
                     to_char(creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en""",
        data.titulo, data.texto_fuente, data.unidad_academica, current_user["id"]
    )
    return dict(row)


@router.get("/", response_model=list[PropuestaOut])
async def listar_propuestas(
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    rows = await db.fetch(
        """SELECT id::text, titulo, texto_fuente, unidad_academica,
                  to_char(creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en
           FROM propuestas
           WHERE creado_por = $1::uuid
           ORDER BY creado_en DESC""",
        current_user["id"]
    )
    return [dict(r) for r in rows]


@router.get("/{propuesta_id}", response_model=PropuestaOut)
async def obtener_propuesta(
    propuesta_id: str,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    row = await db.fetchrow(
        """SELECT id::text, titulo, texto_fuente, unidad_academica,
                  to_char(creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en
           FROM propuestas
           WHERE id = $1::uuid AND creado_por = $2::uuid""",
        propuesta_id, current_user["id"]
    )
    if not row:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    return dict(row)


@router.delete("/{propuesta_id}", status_code=204)
async def eliminar_propuesta(
    propuesta_id: str,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    result = await db.execute(
        "DELETE FROM propuestas WHERE id = $1::uuid AND creado_por = $2::uuid",
        propuesta_id, current_user["id"]
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
