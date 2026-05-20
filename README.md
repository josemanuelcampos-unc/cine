# Evaluador CINE — Backend API

FastAPI + PostgreSQL (Supabase) para el sistema de evaluación CINE de Estudios Propios UNC.

## Setup local

```bash
# 1. Clonar el repo y crear entorno virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (crear archivo .env o exportar)
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
export SECRET_KEY="una-clave-secreta-larga-y-random"

# 4. Levantar
uvicorn main:app --reload
```

La API queda disponible en http://localhost:8000
Documentación interactiva: http://localhost:8000/docs

## Variables de entorno requeridas

| Variable       | Descripción                                              |
|----------------|----------------------------------------------------------|
| `DATABASE_URL` | Connection string de Supabase (con ssl=require implícito)|
| `SECRET_KEY`   | Clave para firmar JWT (mínimo 32 chars, random)          |

## Endpoints principales

| Método | Ruta                    | Descripción                        |
|--------|-------------------------|------------------------------------|
| POST   | /auth/registro          | Crear cuenta de usuario            |
| POST   | /auth/login             | Login (devuelve JWT)               |
| GET    | /auth/me                | Usuario actual                     |
| POST   | /propuestas/            | Crear propuesta                    |
| GET    | /propuestas/            | Listar propuestas del usuario      |
| GET    | /propuestas/{id}        | Detalle de propuesta               |
| DELETE | /propuestas/{id}        | Eliminar propuesta                 |
| POST   | /evaluaciones/          | Crear evaluación                   |
| GET    | /evaluaciones/          | Listar evaluaciones del usuario    |
| GET    | /evaluaciones/{id}      | Detalle de evaluación              |
| PUT    | /evaluaciones/{id}      | Actualizar evaluación              |
| DELETE | /evaluaciones/{id}      | Eliminar evaluación                |

## Deploy en Render

1. Subir este directorio a un repo de GitHub
2. Crear un nuevo "Web Service" en render.com apuntando al repo
3. En Environment Variables, cargar DATABASE_URL y SECRET_KEY
4. El `render.yaml` ya configura build y start command

## Obtener DATABASE_URL desde Supabase

En Supabase → Settings → Database → Connection string → URI
Formato: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
