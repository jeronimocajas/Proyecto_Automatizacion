# models/models.py
import uuid
from datetime import datetime
from sqlalchemy import (Column, String, Boolean, Integer, Numeric, Date,
                        DateTime, Text, BigInteger, ForeignKey, ARRAY)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from core.database import Base

class TipoAuxilio(Base):
    __tablename__ = "tipos_auxilio"
    id          = Column(Integer, primary_key=True)
    codigo      = Column(String(20), unique=True, nullable=False)
    nombre      = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo      = Column(Boolean, default=True)
    creado_en   = Column(DateTime, default=datetime.utcnow)

class DocumentoRequerido(Base):
    __tablename__ = "documentos_requeridos"
    id              = Column(Integer, primary_key=True)
    tipo_auxilio_id = Column(Integer, ForeignKey("tipos_auxilio.id"))
    nombre          = Column(String(150), nullable=False)
    descripcion     = Column(Text)
    obligatorio     = Column(Boolean, default=True)
    orden           = Column(Integer, default=1)
    tipo_auxilio    = relationship("TipoAuxilio")

class Estudiante(Base):
    __tablename__ = "estudiantes"
    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correo_institucional = Column(String(150), unique=True, nullable=False)
    cedula               = Column(String(20), unique=True, nullable=False)
    nombres_apellidos    = Column(String(200))
    programa_academico   = Column(String(150))
    facultad             = Column(String(150))
    verificado           = Column(Boolean, default=False)
    creado_en            = Column(DateTime, default=datetime.utcnow)
    actualizado_en       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tokens               = relationship("TokenSesion", back_populates="estudiante")
    solicitudes          = relationship("Solicitud", back_populates="estudiante")

class TokenSesion(Base):
    __tablename__ = "tokens_sesion"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estudiante_id = Column(UUID(as_uuid=True), ForeignKey("estudiantes.id", ondelete="CASCADE"))
    token         = Column(String(512), unique=True, nullable=False)
    expira_en     = Column(DateTime, nullable=False)
    usado         = Column(Boolean, default=False)
    ip_origen     = Column(INET)
    creado_en     = Column(DateTime, default=datetime.utcnow)
    estudiante    = relationship("Estudiante", back_populates="tokens")

class Solicitud(Base):
    __tablename__ = "solicitudes"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estudiante_id   = Column(UUID(as_uuid=True), ForeignKey("estudiantes.id"))
    token_id        = Column(UUID(as_uuid=True), ForeignKey("tokens_sesion.id"))
    tipo_auxilio_id = Column(Integer, ForeignKey("tipos_auxilio.id"))

    # Datos personales del formulario
    fecha_solicitud         = Column(Date, default=datetime.utcnow)
    lugar_nacimiento        = Column(String(100))
    fecha_nacimiento        = Column(Date)
    edad                    = Column(Integer)
    estado_civil            = Column(String(30))
    direccion               = Column(String(200))
    barrio                  = Column(String(100))
    ciudad_municipio        = Column(String(100))
    celular                 = Column(String(20))

    # Información académica
    programa_academico      = Column(String(150))
    facultad                = Column(String(150))
    promedio_semestral      = Column(Numeric(4, 2))
    promedio_acumulado      = Column(Numeric(4, 2))
    semestre_a_cursar       = Column(Integer)

    # Población inclusiva
    poblacion_mujer_cabeza  = Column(Boolean, default=False)
    poblacion_afrocolombiano= Column(Boolean, default=False)
    poblacion_indigena      = Column(Boolean, default=False)
    poblacion_room          = Column(Boolean, default=False)
    poblacion_victima       = Column(Boolean, default=False)
    poblacion_lgtbiq        = Column(Boolean, default=False)
    poblacion_ninguna       = Column(Boolean, default=False)

    # Discapacidad
    discapacidad_motora     = Column(Boolean, default=False)
    discapacidad_sensorial  = Column(Boolean, default=False)
    discapacidad_emocional  = Column(Boolean, default=False)
    discapacidad_cognitiva  = Column(Boolean, default=False)
    discapacidad_ninguna    = Column(Boolean, default=False)

    # Información familiar
    nombre_padre            = Column(String(200))
    ocupacion_padre         = Column(String(100))
    empresa_padre           = Column(String(100))
    direccion_padre         = Column(String(200))
    telefono_padre          = Column(String(20))
    nombre_madre            = Column(String(200))
    ocupacion_madre         = Column(String(100))
    empresa_madre           = Column(String(100))
    direccion_madre         = Column(String(200))
    telefono_madre          = Column(String(20))
    lugar_residencia_familia= Column(String(200))
    num_personas_nucleo     = Column(Integer)
    num_personas_contribuyen= Column(Integer)

    # Socioeconómica
    ingreso_mensual_solicitante = Column(Numeric(12, 2))
    egreso_mensual_solicitante  = Column(Numeric(12, 2))
    ingreso_mensual_dependencia = Column(Numeric(12, 2))
    egreso_mensual_dependencia  = Column(Numeric(12, 2))
    tiene_credito_icetex        = Column(Boolean, default=False)

    motivo_solicitud        = Column(Text)

    # Estado y control
    estado                  = Column(String(30), default="PENDIENTE")
    intentos                = Column(Integer, default=0)
    max_intentos            = Column(Integer, default=2)

    # Resultado IA
    resultado_validacion    = Column(JSONB)
    observaciones_ia        = Column(Text)
    campos_faltantes        = Column(JSONB)

    # Correo
    correo_destino          = Column(String(150), default="bienestar@cecar.edu.co")
    correo_enviado          = Column(Boolean, default=False)
    fecha_envio_correo      = Column(DateTime)

    creado_en               = Column(DateTime, default=datetime.utcnow)
    actualizado_en          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    estudiante              = relationship("Estudiante", back_populates="solicitudes")
    archivos                = relationship("ArchivoSolicitud", back_populates="solicitud")
    validaciones            = relationship("ValidacionIA", back_populates="solicitud")

class ArchivoSolicitud(Base):
    __tablename__ = "archivos_solicitud"
    id                     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solicitud_id           = Column(UUID(as_uuid=True), ForeignKey("solicitudes.id", ondelete="CASCADE"))
    documento_requerido_id = Column(Integer, ForeignKey("documentos_requeridos.id"))
    nombre_original        = Column(String(300), nullable=False)
    nombre_almacenado      = Column(String(300), nullable=False)
    ruta_almacenamiento    = Column(String(500), nullable=False)
    tipo_mime              = Column(String(100))
    tamanio_bytes          = Column(BigInteger)
    hash_sha256            = Column(String(64))
    intento_numero         = Column(Integer, default=1)
    creado_en              = Column(DateTime, default=datetime.utcnow)
    solicitud              = relationship("Solicitud", back_populates="archivos")

class ValidacionIA(Base):
    __tablename__ = "validaciones_ia"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solicitud_id     = Column(UUID(as_uuid=True), ForeignKey("solicitudes.id", ondelete="CASCADE"))
    intento_numero   = Column(Integer, nullable=False)
    modelo_ia        = Column(String(100), default="claude-sonnet-4-20250514")
    prompt_enviado   = Column(Text)
    respuesta_ia     = Column(JSONB)
    resultado        = Column(String(20))
    campos_invalidos = Column(JSONB)
    tiempo_ms        = Column(Integer)
    creado_en        = Column(DateTime, default=datetime.utcnow)
    solicitud        = relationship("Solicitud", back_populates="validaciones")

class LogCorreo(Base):
    __tablename__ = "log_correos"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solicitud_id = Column(UUID(as_uuid=True), ForeignKey("solicitudes.id"))
    destinatario = Column(String(150), nullable=False)
    asunto       = Column(String(300))
    estado       = Column(String(20))


class Convocatoria(Base):
    __tablename__ = "convocatorias"
    id           = Column(Integer, primary_key=True)
    nombre       = Column(String(150), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin    = Column(Date, nullable=False)
    activa       = Column(Boolean, default=False)
    creado_en    = Column(DateTime, default=datetime.utcnow)
