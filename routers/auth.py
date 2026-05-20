"""
Router de autenticación: login, registro, usuario actual
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import asyncpg

from database import get_db
from auth_utils import hash_password, verify_password, create_access_token, decode_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Schemas ────────────────────────────────────────────────

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


# ── Dependencia: usuario actual desde JWT ──────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: asyncpg.Connection = Depends(get_db)
) -> dict:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    user = await db.fetchrow(
        "SELECT id::text, email, nombre, rol FROM usuarios WHERE id = $1::uuid AND activo = TRUE",
        payload.get("sub")
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return dict(user)


# ── Endpoints ──────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: asyncpg.Connection = Depends(get_db)
):
    user = await db.fetchrow(
        "SELECT id::text, email, nombre, rol, password_hash FROM usuarios WHERE email = $1 AND activo = TRUE",
        form.username
    )
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    token = create_access_token({"sub": user["id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": user["id"], "email": user["email"], "nombre": user["nombre"], "rol": user["rol"]}
    }


@router.post("/registro", response_model=UsuarioOut, status_code=201)
async def registro(
    data: UsuarioCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    existing = await db.fetchrow("SELECT id FROM usuarios WHERE email = $1", data.email)
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    row = await db.fetchrow(
        """INSERT INTO usuarios (email, nombre, password_hash)
           VALUES ($1, $2, $3)
           RETURNING id::text, email, nombre, rol""",
        data.email, data.nombre, hash_password(data.password)
    )
    return dict(row)


@router.get("/me", response_model=UsuarioOut)
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
