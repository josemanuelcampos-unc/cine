"""
Router de autenticación usando Supabase REST API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import httpx
import json

from database import get_db
from auth_utils import hash_password, verify_password, create_access_token, decode_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class UsuarioCreate(BaseModel):
    email: str
    nombre: str
    password: str

class UsuarioOut(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioOut


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: httpx.AsyncClient = Depends(get_db)
) -> dict:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    r = await db.get(f"/usuarios?id=eq.{payload.get('sub')}&activo=eq.true&select=id,email,nombre,rol")
    users = r.json()
    if not users:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return users[0]


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: httpx.AsyncClient = Depends(get_db)
):
    r = await db.get(f"/usuarios?email=eq.{form.username}&activo=eq.true&select=id,email,nombre,rol,password_hash")
    users = r.json()
    if not users or not verify_password(form.password, users[0]["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    user = users[0]
    token = create_access_token({"sub": user["id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": user["id"], "email": user["email"], "nombre": user["nombre"], "rol": user["rol"]}
    }


@router.post("/registro", response_model=UsuarioOut, status_code=201)
async def registro(
    data: UsuarioCreate,
    db: httpx.AsyncClient = Depends(get_db)
):
    existing = await db.get(f"/usuarios?email=eq.{data.email}&select=id")
    if existing.json():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    r = await db.post("/usuarios", content=json.dumps({
        "email": data.email,
        "nombre": data.nombre,
        "password_hash": hash_password(data.password),
        "rol": "evaluador",
        "activo": True
    }))
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail="Error al crear usuario")
    return r.json()[0]


@router.get("/me", response_model=UsuarioOut)
async def me(current_user: dict = Depends(get_current_user)):
    return current_user

