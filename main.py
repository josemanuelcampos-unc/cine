"""
Evaluador CINE — Backend FastAPI
Secretaría de Asuntos Académicos, UNC
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import os

from database import get_db, init_db
from routers import auth, propuestas, evaluaciones
from models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Evaluador CINE — API",
    description="Backend para el sistema de evaluación CINE de Estudios Propios UNC",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — en producción reemplazá el "*" por el dominio del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(propuestas.router,   prefix="/propuestas",   tags=["Propuestas"])
app.include_router(evaluaciones.router, prefix="/evaluaciones", tags=["Evaluaciones"])


@app.get("/")
def health():
    return {"status": "ok", "sistema": "Evaluador CINE UNC v1.0"}
