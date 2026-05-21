"""
Router de evaluaciones usando Supabase REST API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import httpx
import json

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


class EvaluacionUpsert(BaseModel):
    propuesta_id: str
    estado: Optional[str] = "borrador"
    scores: Optional[dict[str, Any]] = {}
    meta: Optional[dict[str, Any]] = {}
    multi_sel: Optional[dict[str, Any]] = {}
    ai_razones: Optional[dict[str, Any]] = {}
    ai_sintesis: Optional[str] = None
    nivel_cine: Optional[int] = None
    promedio: Optional[float] = None
    tipologia: Optional[str] = None
    alertas_activas: Optional[list] = []


@router.post("/", status_code=201)
async def crear_evaluacion(
    data: EvaluacionUpsert,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.post("/evaluaciones", content=json.dumps({
        "propuesta_id": data.propuesta_id,
        "evaluador_id": current_user["id"],
        "estado": data.estado,
        "scores": data.scores,
        "meta": data.meta,
        "multi_sel": data.multi_sel,
        "ai_razones": data.ai_razones,
        "ai_sintesis": data.ai_sintesis,
        "nivel_cine": data.nivel_cine,
        "promedio": data.promedio,
        "tipologia": data.tipologia,
        "alertas_activas": data.alertas_activas or []
    }))
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Error: {r.text}")
    return r.json()[0]


@router.get("/")
async def listar_evaluaciones(
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.get(f"/evaluaciones?evaluador_id=eq.{current_user['id']}&order=actualizado_en.desc")
    return r.json()


@router.get("/{eval_id}")
async def obtener_evaluacion(
    eval_id: str,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.get(f"/evaluaciones?id=eq.{eval_id}&evaluador_id=eq.{current_user['id']}")
    rows = r.json()
    if not rows:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return rows[0]


@router.put("/{eval_id}")
async def actualizar_evaluacion(
    eval_id: str,
    data: EvaluacionUpsert,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.patch(
        f"/evaluaciones?id=eq.{eval_id}&evaluador_id=eq.{current_user['id']}",
        content=json.dumps({
            "estado": data.estado,
            "scores": data.scores,
            "meta": data.meta,
            "multi_sel": data.multi_sel,
            "ai_razones": data.ai_razones,
            "ai_sintesis": data.ai_sintesis,
            "nivel_cine": data.nivel_cine,
            "promedio": data.promedio,
            "tipologia": data.tipologia,
            "alertas_activas": data.alertas_activas or []
        })
    )
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    rows = r.json()
    return rows[0] if rows else {"ok": True}


@router.delete("/{eval_id}", status_code=204)
async def eliminar_evaluacion(
    eval_id: str,
    current_user: dict = Depends(get_current_user),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.delete(f"/evaluaciones?id=eq.{eval_id}&evaluador_id=eq.{current_user['id']}")
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

