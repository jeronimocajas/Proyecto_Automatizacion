-- ============================================================
-- SISTEMA DE AUXILIOS ECONÓMICOS - CECAR
-- Base de Datos PostgreSQL
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------
-- TIPOS DE AUXILIO
-- ------------------------------------------------------------
CREATE TABLE tipos_auxilio (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(20) UNIQUE NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    descripcion   TEXT,
    activo        BOOLEAN DEFAULT TRUE,
    creado_en     TIMESTAMP DEFAULT NOW()
);

INSERT INTO tipos_auxilio (codigo, nombre, descripcion) VALUES
    ('ESPECIAL',    'Auxilio Especial',            'Apoyo económico para estudiantes en situación de vulnerabilidad especial'),
    ('PLAN_PADRINO','Plan Padrino',                'Apoyo para estudiantes con patrocinador externo o interno'),
    ('INCLUSION',   'Auxilio de Inclusión',        'Apoyo para estudiantes de poblaciones inclusivas o con discapacidad');

-- ------------------------------------------------------------
-- DOCUMENTOS REQUERIDOS POR TIPO DE AUXILIO
-- ------------------------------------------------------------
CREATE TABLE documentos_requeridos (
    id              SERIAL PRIMARY KEY,
    tipo_auxilio_id INTEGER REFERENCES tipos_auxilio(id),
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    obligatorio     BOOLEAN DEFAULT TRUE,
    orden           INTEGER DEFAULT 1
);

INSERT INTO documentos_requeridos (tipo_auxilio_id, nombre, descripcion, obligatorio, orden) VALUES
-- Auxilio Especial
(1, 'Formulario F-BI-011',         'Formulario de solicitud de auxilio diligenciado y firmado', TRUE, 1),
(1, 'Fotocopia Cédula',            'Documento de identidad vigente', TRUE, 2),
(1, 'Certificado de notas',        'Certificado con promedio acumulado (mínimo 3.7)', TRUE, 3),
(1, 'Carta de exposición de motivos', 'Escrito detallando la situación económica', TRUE, 4),
(1, 'Comprobante de ingresos familia', 'Desprendibles de nómina o declaración de ingresos', TRUE, 5),
-- Plan Padrino
(2, 'Formulario F-BI-011',         'Formulario de solicitud de auxilio diligenciado y firmado', TRUE, 1),
(2, 'Fotocopia Cédula',            'Documento de identidad vigente', TRUE, 2),
(2, 'Certificado de notas',        'Certificado con promedio acumulado (mínimo 3.7)', TRUE, 3),
(2, 'Carta del padrino',           'Carta de compromiso del patrocinador', TRUE, 4),
(2, 'Documentos del padrino',      'Cédula y comprobante de ingresos del padrino', TRUE, 5),
-- Inclusión
(3, 'Formulario F-BI-011',         'Formulario de solicitud de auxilio diligenciado y firmado', TRUE, 1),
(3, 'Fotocopia Cédula',            'Documento de identidad vigente', TRUE, 2),
(3, 'Certificado de notas',        'Certificado con promedio acumulado (mínimo 3.7)', TRUE, 3),
(3, 'Certificado de discapacidad', 'Certificado médico o de entidad competente (si aplica)', FALSE, 4),
(3, 'Certificado población especial', 'Documentación que acredite condición (víctima, LGTBIQ+, afrocolombiano, indígena, etc.)', FALSE, 5);

-- ------------------------------------------------------------
-- ESTUDIANTES (identidad verificada)
-- ------------------------------------------------------------
CREATE TABLE estudiantes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correo_institucional VARCHAR(150) UNIQUE NOT NULL CHECK (correo_institucional LIKE '%@cecar.edu.co'),
    cedula              VARCHAR(20) UNIQUE NOT NULL,
    nombres_apellidos   VARCHAR(200),
    programa_academico  VARCHAR(150),
    facultad            VARCHAR(150),
    verificado          BOOLEAN DEFAULT FALSE,
    creado_en           TIMESTAMP DEFAULT NOW(),
    actualizado_en      TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- TOKENS DE SESIÓN (24h de vida máxima)
-- ------------------------------------------------------------
CREATE TABLE tokens_sesion (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estudiante_id   UUID REFERENCES estudiantes(id) ON DELETE CASCADE,
    token           VARCHAR(512) UNIQUE NOT NULL,
    expira_en       TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
    usado           BOOLEAN DEFAULT FALSE,
    ip_origen       INET,
    creado_en       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tokens_token ON tokens_sesion(token);
CREATE INDEX idx_tokens_expira ON tokens_sesion(expira_en);

-- ------------------------------------------------------------
-- SOLICITUDES DE AUXILIO
-- ------------------------------------------------------------
CREATE TABLE solicitudes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estudiante_id       UUID REFERENCES estudiantes(id),
    token_id            UUID REFERENCES tokens_sesion(id),
    tipo_auxilio_id     INTEGER REFERENCES tipos_auxilio(id),

    -- Datos del formulario F-BI-011
    fecha_solicitud             DATE DEFAULT CURRENT_DATE,
    lugar_nacimiento            VARCHAR(100),
    fecha_nacimiento            DATE,
    edad                        INTEGER,
    estado_civil                VARCHAR(30),  -- Soltero, Casado, Unión libre, Divorciado, Viudo
    direccion                   VARCHAR(200),
    barrio                      VARCHAR(100),
    ciudad_municipio            VARCHAR(100),
    celular                     VARCHAR(20),

    -- Información académica
    programa_academico          VARCHAR(150),
    facultad                    VARCHAR(150),
    promedio_semestral          NUMERIC(4,2),
    promedio_acumulado          NUMERIC(4,2),
    semestre_a_cursar           INTEGER,

    -- Datos de población inclusiva (solo uno puede ser TRUE)
    poblacion_mujer_cabeza      BOOLEAN DEFAULT FALSE,
    poblacion_afrocolombiano    BOOLEAN DEFAULT FALSE,
    poblacion_indigena          BOOLEAN DEFAULT FALSE,
    poblacion_room              BOOLEAN DEFAULT FALSE,
    poblacion_victima           BOOLEAN DEFAULT FALSE,
    poblacion_lgtbiq            BOOLEAN DEFAULT FALSE,
    poblacion_ninguna           BOOLEAN DEFAULT FALSE,

    -- Datos de discapacidad (solo uno puede ser TRUE)
    discapacidad_motora         BOOLEAN DEFAULT FALSE,
    discapacidad_sensorial      BOOLEAN DEFAULT FALSE,
    discapacidad_emocional      BOOLEAN DEFAULT FALSE,
    discapacidad_cognitiva      BOOLEAN DEFAULT FALSE,
    discapacidad_ninguna        BOOLEAN DEFAULT FALSE,

    -- Información familiar
    nombre_padre                VARCHAR(200),
    ocupacion_padre             VARCHAR(100),
    empresa_padre               VARCHAR(100),
    direccion_padre             VARCHAR(200),
    telefono_padre              VARCHAR(20),
    nombre_madre                VARCHAR(200),
    ocupacion_madre             VARCHAR(100),
    empresa_madre               VARCHAR(100),
    direccion_madre             VARCHAR(200),
    telefono_madre              VARCHAR(20),
    lugar_residencia_familia    VARCHAR(200),
    num_personas_nucleo         INTEGER,
    num_personas_contribuyen    INTEGER,

    -- Información socioeconómica
    ingreso_mensual_solicitante NUMERIC(12,2),
    egreso_mensual_solicitante  NUMERIC(12,2),
    ingreso_mensual_dependencia NUMERIC(12,2),
    egreso_mensual_dependencia  NUMERIC(12,2),
    tiene_credito_icetex        BOOLEAN DEFAULT FALSE,

    -- Motivo de la solicitud
    motivo_solicitud            TEXT,

    -- Estado del proceso
    estado                      VARCHAR(30) DEFAULT 'PENDIENTE',
    -- PENDIENTE, VALIDANDO, APROBADO, RECHAZADO, ENVIADO, ERROR_VALIDACION

    intentos                    INTEGER DEFAULT 0,
    max_intentos                INTEGER DEFAULT 2,

    -- Resultado de la validación IA
    resultado_validacion        JSONB,
    observaciones_ia            TEXT,
    campos_faltantes            JSONB,

    -- Envío de correo
    correo_destino              VARCHAR(150) DEFAULT 'bienestar@cecar.edu.co',
    correo_enviado              BOOLEAN DEFAULT FALSE,
    fecha_envio_correo          TIMESTAMP,

    creado_en                   TIMESTAMP DEFAULT NOW(),
    actualizado_en              TIMESTAMP DEFAULT NOW(),

    -- RESTRICCIÓN: un estudiante solo puede tener una solicitud activa
    CONSTRAINT una_solicitud_activa UNIQUE (estudiante_id, estado)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_solicitudes_estudiante ON solicitudes(estudiante_id);
CREATE INDEX idx_solicitudes_estado ON solicitudes(estado);
CREATE INDEX idx_solicitudes_tipo ON solicitudes(tipo_auxilio_id);

-- ------------------------------------------------------------
-- ARCHIVOS CARGADOS POR SOLICITUD
-- ------------------------------------------------------------
CREATE TABLE archivos_solicitud (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id            UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    documento_requerido_id  INTEGER REFERENCES documentos_requeridos(id),
    nombre_original         VARCHAR(300) NOT NULL,
    nombre_almacenado       VARCHAR(300) NOT NULL,
    ruta_almacenamiento     VARCHAR(500) NOT NULL,
    tipo_mime               VARCHAR(100),
    tamanio_bytes           BIGINT,
    hash_sha256             VARCHAR(64),  -- Para detectar duplicados o alteraciones
    intento_numero          INTEGER DEFAULT 1,
    creado_en               TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- HISTORIAL DE VALIDACIONES IA
-- ------------------------------------------------------------
CREATE TABLE validaciones_ia (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id        UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    intento_numero      INTEGER NOT NULL,
    modelo_ia           VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',
    prompt_enviado      TEXT,
    respuesta_ia        JSONB,
    resultado           VARCHAR(20),  -- APROBADO, RECHAZADO, REVISION
    campos_invalidos    JSONB,
    tiempo_ms           INTEGER,
    creado_en           TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- LOG DE CORREOS ENVIADOS
-- ------------------------------------------------------------
CREATE TABLE log_correos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id    UUID REFERENCES solicitudes(id),
    destinatario    VARCHAR(150) NOT NULL,
    asunto          VARCHAR(300),
    estado          VARCHAR(20),  -- ENVIADO, ERROR
    error_detalle   TEXT,
    creado_en       TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
-- FUNCIÓN: actualizar campo updated_at automáticamente
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_estudiantes_updated
    BEFORE UPDATE ON estudiantes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_solicitudes_updated
    BEFORE UPDATE ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ------------------------------------------------------------
-- VISTA ÚTIL: resumen de solicitudes
-- ------------------------------------------------------------
CREATE VIEW v_solicitudes_resumen AS
SELECT
    s.id,
    e.correo_institucional,
    e.cedula,
    ta.nombre AS tipo_auxilio,
    s.estado,
    s.intentos,
    s.promedio_acumulado,
    s.correo_enviado,
    s.fecha_envio_correo,
    s.creado_en,
    s.actualizado_en
FROM solicitudes s
JOIN estudiantes e ON e.id = s.estudiante_id
JOIN tipos_auxilio ta ON ta.id = s.tipo_auxilio_id;
