"""
Router de propuestas usando Supabase REST API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import json

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


class PropuestaCreate(BaseModel):
    titulo: str
    texto_fuente: Optional[str] = None
    unidad_academica: Optional[str] = None


@router.post("/", status_code=201)
async def crear_propuesta(
    data: PropuestaCreate,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.post("/propuestas", content=json.dumps({
        "titulo": data.titulo,
        "texto_fuente": data.texto_fuente,
        "unidad_academica": data.unidad_academica,
        "creado_por": current_user["id"]
    }))
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail="Error al crear propuesta")
    return r.json()[0]


@router.get("/")
async def listar_propuestas(
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.get(f"/propuestas?creado_por=eq.{current_user['id']}&order=creado_en.desc")
    return r.json()


@router.get("/{propuesta_id}")
async def obtener_propuesta(
    propuesta_id: str,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.get(f"/propuestas?id=eq.{propuesta_id}&creado_por=eq.{current_user['id']}")
    rows = r.json()
    if not rows:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    return rows[0]


@router.delete("/{propuesta_id}", status_code=204)
async def eliminar_propuesta(
    propuesta_id: str,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.delete(f"/propuestas?id=eq.{propuesta_id}&creado_por=eq.{current_user['id']}")
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

