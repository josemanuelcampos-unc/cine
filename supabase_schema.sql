-- ============================================================
-- Evaluador CINE — Schema Supabase
-- ============================================================

-- Usuarios del sistema
CREATE TABLE usuarios (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  nombre      TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  rol         TEXT NOT NULL DEFAULT 'evaluador',  -- 'evaluador' | 'admin'
  activo      BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Propuestas curriculares cargadas
CREATE TABLE propuestas (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo            TEXT NOT NULL,
  texto_fuente      TEXT,                    -- texto extraído del PDF/Word
  unidad_academica  TEXT,
  creado_por        UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Evaluaciones CINE (una por propuesta, puede tener múltiples versiones)
CREATE TABLE evaluaciones (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  propuesta_id    UUID REFERENCES propuestas(id) ON DELETE CASCADE,
  evaluador_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  estado          TEXT NOT NULL DEFAULT 'borrador',  -- 'borrador' | 'finalizado'

  -- Scores de los 8 campos (JSONB para flexibilidad)
  scores          JSONB NOT NULL DEFAULT '{}',
  -- Ejemplo: {"req_ingreso": 3, "objetivos": 4, "contenidos": 4,
  --           "bibliografia": 3, "metodologia": 2, "aprobacion": 4,
  --           "objeto": 4, "carga": 2}

  -- Metadatos de la propuesta evaluada
  meta            JSONB NOT NULL DEFAULT '{}',
  -- Ejemplo: {"orientacion": "FC", "esMC": false, "destinatarios": ["Graduados"],
  --           "horasInteraccion": 60, "horasAutonomas": 20,
  --           "necesidadFormativa": true, "proc1": "Ciencias Sociales"}

  -- Selecciones múltiples (campos tipo 'multiple')
  multi_sel       JSONB NOT NULL DEFAULT '{}',

  -- Razones generadas por IA para cada campo
  ai_razones      JSONB NOT NULL DEFAULT '{}',

  -- Síntesis narrativa (generada por IA o escrita manualmente)
  ai_sintesis     TEXT,

  -- Resultado calculado
  nivel_cine      INT,           -- 4, 5, 6 o 7
  promedio        NUMERIC(4,2),  -- promedio ponderado
  tipologia       TEXT,          -- 'consistente' | 'tensiones' | 'inconsistente' | 'no_determinable'
  alertas_activas JSONB,         -- lista de IDs de alertas que dispararon

  creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger para actualizar actualizado_en automáticamente
CREATE OR REPLACE FUNCTION update_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
  NEW.actualizado_en = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_propuestas_updated
  BEFORE UPDATE ON propuestas
  FOR EACH ROW EXECUTE FUNCTION update_actualizado_en();

CREATE TRIGGER trg_evaluaciones_updated
  BEFORE UPDATE ON evaluaciones
  FOR EACH ROW EXECUTE FUNCTION update_actualizado_en();

-- Índices útiles
CREATE INDEX idx_evaluaciones_propuesta ON evaluaciones(propuesta_id);
CREATE INDEX idx_evaluaciones_evaluador ON evaluaciones(evaluador_id);
CREATE INDEX idx_evaluaciones_estado    ON evaluaciones(estado);
CREATE INDEX idx_propuestas_creador     ON propuestas(creado_por);

-- ============================================================
-- Row Level Security (RLS) — cada usuario ve solo lo suyo
-- IMPORTANTE: esto usa el JWT del backend, no el de Supabase Auth
-- Por ahora lo dejamos desactivado; el backend maneja la autorización
-- ============================================================
-- ALTER TABLE propuestas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE evaluaciones ENABLE ROW LEVEL SECURITY;
