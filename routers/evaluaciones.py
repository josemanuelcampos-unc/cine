"""
Router de evaluaciones CINE
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import asyncpg
import json

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────

class EvaluacionUpsert(BaseModel):
    propuesta_id: str
    estado: Optional[str] = "borrador"     # 'borrador' | 'finalizado'
    scores: Optional[dict[str, Any]] = {}
    meta: Optional[dict[str, Any]] = {}
    multi_sel: Optional[dict[str, Any]] = {}
    ai_razones: Optional[dict[str, Any]] = {}
    ai_sintesis: Optional[str] = None
    nivel_cine: Optional[int] = None
    promedio: Optional[float] = None
    tipologia: Optional[str] = None
    alertas_activas: Optional[list[str]] = []


class EvaluacionOut(BaseModel):
    id: str
    propuesta_id: str
    estado: str
    scores: dict
    meta: dict
    multi_sel: dict
    ai_razones: dict
    ai_sintesis: Optional[str]
    nivel_cine: Optional[int]
    promedio: Optional[float]
    tipologia: Optional[str]
    alertas_activas: Optional[list]
    creado_en: str
    actualizado_en: str


# ── Helpers ────────────────────────────────────────────────

def row_to_eval(row) -> dict:
    d = dict(row)
    for key in ("scores", "meta", "multi_sel", "ai_razones", "alertas_activas"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
        elif d.get(key) is None:
            d[key] = {} if key != "alertas_activas" else []
    return d


# ── Endpoints ──────────────────────────────────────────────

@router.post("/", status_code=201)
async def crear_evaluacion(
    data: EvaluacionUpsert,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    # Verificar que la propuesta le pertenece
    prop = await db.fetchrow(
        "SELECT id FROM propuestas WHERE id = $1::uuid AND creado_por = $2::uuid",
        data.propuesta_id, current_user["id"]
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    row = await db.fetchrow(
        """INSERT INTO evaluaciones
             (propuesta_id, evaluador_id, estado, scores, meta, multi_sel,
              ai_razones, ai_sintesis, nivel_cine, promedio, tipologia, alertas_activas)
           VALUES
             ($1::uuid, $2::uuid, $3, $4::jsonb, $5::jsonb, $6::jsonb,
              $7::jsonb, $8, $9, $10, $11, $12::jsonb)
           RETURNING
             id::text, propuesta_id::text, estado,
             scores::text, meta::text, multi_sel::text,
             ai_razones::text, ai_sintesis, nivel_cine, promedio, tipologia,
             alertas_activas::text,
             to_char(creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en,
             to_char(actualizado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as actualizado_en""",
        data.propuesta_id, current_user["id"], data.estado,
        json.dumps(data.scores), json.dumps(data.meta), json.dumps(data.multi_sel),
        json.dumps(data.ai_razones), data.ai_sintesis, data.nivel_cine,
        data.promedio, data.tipologia, json.dumps(data.alertas_activas or [])
    )
    return row_to_eval(row)


@router.get("/")
async def listar_evaluaciones(
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    rows = await db.fetch(
        """SELECT
             e.id::text, e.propuesta_id::text, e.estado,
             e.scores::text, e.meta::text, e.multi_sel::text,
             e.ai_razones::text, e.ai_sintesis, e.nivel_cine, e.promedio,
             e.tipologia, e.alertas_activas::text,
             to_char(e.creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en,
             to_char(e.actualizado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as actualizado_en,
             p.titulo as propuesta_titulo
           FROM evaluaciones e
           JOIN propuestas p ON p.id = e.propuesta_id
           WHERE e.evaluador_id = $1::uuid
           ORDER BY e.actualizado_en DESC""",
        current_user["id"]
    )
    result = []
    for r in rows:
        d = row_to_eval(r)
        result.append(d)
    return result


@router.get("/{eval_id}")
async def obtener_evaluacion(
    eval_id: str,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    row = await db.fetchrow(
        """SELECT
             e.id::text, e.propuesta_id::text, e.estado,
             e.scores::text, e.meta::text, e.multi_sel::text,
             e.ai_razones::text, e.ai_sintesis, e.nivel_cine, e.promedio,
             e.tipologia, e.alertas_activas::text,
             to_char(e.creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en,
             to_char(e.actualizado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as actualizado_en
           FROM evaluaciones e
           WHERE e.id = $1::uuid AND e.evaluador_id = $2::uuid""",
        eval_id, current_user["id"]
    )
    if not row:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return row_to_eval(row)


@router.put("/{eval_id}")
async def actualizar_evaluacion(
    eval_id: str,
    data: EvaluacionUpsert,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    row = await db.fetchrow(
        """UPDATE evaluaciones SET
             estado = $3,
             scores = $4::jsonb,
             meta = $5::jsonb,
             multi_sel = $6::jsonb,
             ai_razones = $7::jsonb,
             ai_sintesis = $8,
             nivel_cine = $9,
             promedio = $10,
             tipologia = $11,
             alertas_activas = $12::jsonb
           WHERE id = $1::uuid AND evaluador_id = $2::uuid
           RETURNING
             id::text, propuesta_id::text, estado,
             scores::text, meta::text, multi_sel::text,
             ai_razones::text, ai_sintesis, nivel_cine, promedio, tipologia,
             alertas_activas::text,
             to_char(creado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as creado_en,
             to_char(actualizado_en, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as actualizado_en""",
        eval_id, current_user["id"], data.estado,
        json.dumps(data.scores), json.dumps(data.meta), json.dumps(data.multi_sel),
        json.dumps(data.ai_razones), data.ai_sintesis, data.nivel_cine,
        data.promedio, data.tipologia, json.dumps(data.alertas_activas or [])
    )
    if not row:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return row_to_eval(row)


@router.delete("/{eval_id}", status_code=204)
async def eliminar_evaluacion(
    eval_id: str,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    result = await db.execute(
        "DELETE FROM evaluaciones WHERE id = $1::uuid AND evaluador_id = $2::uuid",
        eval_id, current_user["id"]
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
