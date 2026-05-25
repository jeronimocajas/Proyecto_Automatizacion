# -*- coding: utf-8 -*-
# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
import secrets
import random

from core.database import get_db
from core.config import settings
from models.models import Estudiante, TokenSesion

router = APIRouter()

# -- Schemas --------------------------------------------------
class LoginRequest(BaseModel):
    correo_institucional: str
    cedula: str

    @field_validator("correo_institucional")
    @classmethod
    def validar_dominio(cls, v: str) -> str:
        if not v.endswith(settings.DOMINIO_CORREO):
            raise ValueError(f"El correo debe ser del dominio {settings.DOMINIO_CORREO}")
        return v.lower().strip()

    @field_validator("cedula")
    @classmethod
    def validar_cedula(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not v.isdigit() or len(v) < 6 or len(v) > 15:
            raise ValueError("Cedula invalida")
        return v

class TokenResponse(BaseModel):
    token: str
    expira_en: datetime
    estudiante_id: str
    mensaje: str

class VerificarTokenRequest(BaseModel):
    token: str

class SolicitarCodigoRequest(BaseModel):
    correo_institucional: str
    cedula: str

    @field_validator("correo_institucional")
    @classmethod
    def val_dominio(cls, v: str) -> str:
        if not v.endswith(settings.DOMINIO_CORREO):
            raise ValueError(f"El correo debe ser del dominio {settings.DOMINIO_CORREO}")
        return v.lower().strip()

    @field_validator("cedula")
    @classmethod
    def val_cedula(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not v.isdigit() or len(v) < 6 or len(v) > 15:
            raise ValueError("Cedula invalida")
        return v

class VerificarCodigoRequest(BaseModel):
    correo_institucional: str
    cedula: str
    codigo: str

# -- Utilidades ------------------------------------------------
def generar_token() -> str:
    return secrets.token_hex(64)

async def obtener_estudiante_por_token(token: str, db: AsyncSession):
    result = await db.execute(
        select(TokenSesion).where(
            TokenSesion.token == token,
            TokenSesion.expira_en > datetime.utcnow(),
            TokenSesion.usado == False
        )
    )
    tok = result.scalar_one_or_none()
    if not tok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido, expirado o ya utilizado."
        )
    result2 = await db.execute(select(Estudiante).where(Estudiante.id == tok.estudiante_id))
    estudiante = result2.scalar_one_or_none()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")
    return estudiante, tok

# -- Endpoints OTP ---------------------------------------------
@router.post("/solicitar-codigo", summary="Enviar codigo OTP al correo del estudiante")
async def solicitar_codigo(data: SolicitarCodigoRequest, db: AsyncSession = Depends(get_db)):
    from services.correo import enviar_codigo_verificacion

    # Invalidar codigos anteriores del mismo correo
    await db.execute(text("""
        UPDATE codigos_verificacion SET usado = TRUE
        WHERE correo = :correo AND usado = FALSE
    """), {"correo": data.correo_institucional})

    # Generar codigo de 6 digitos
    codigo = str(random.randint(100000, 999999))
    expira = datetime.utcnow() + timedelta(minutes=10)

    await db.execute(text("""
    INSERT INTO codigos_verificacion (correo, cedula, codigo, expira_en)
    VALUES (:correo, :cedula, :codigo, :expira)
"""), {"correo": data.correo_institucional, "cedula": data.cedula, "codigo": codigo, "expira": expira})
    await db.commit()

    ok = enviar_codigo_verificacion(data.correo_institucional, codigo)
    if not ok:
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el correo de verificacion. Revisa tu direccion e intenta de nuevo."
        )

    return {"mensaje": "Codigo enviado. Revisa tu correo institucional. Expira en 10 minutos."}


@router.post("/verificar-codigo", summary="Verificar OTP y generar token de sesion")
async def verificar_codigo(data: VerificarCodigoRequest, request: Request, db: AsyncSession = Depends(get_db)):

    result = await db.execute(text("""
        SELECT id, codigo, intentos FROM codigos_verificacion
        WHERE correo = :correo AND cedula = :cedula
        AND usado = FALSE AND expira_en > NOW()
        ORDER BY creado_en DESC LIMIT 1
    """), {"correo": data.correo_institucional, "cedula": data.cedula})
    row = result.mappings().fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="No hay un codigo activo para este correo. Solicita uno nuevo.")

    if row["intentos"] >= 3:
        await db.execute(text("UPDATE codigos_verificacion SET usado = TRUE WHERE id = :id"), {"id": row["id"]})
        await db.commit()
        raise HTTPException(status_code=400, detail="Demasiados intentos fallidos. Solicita un nuevo codigo.")

    if data.codigo.strip() != row["codigo"]:
        nuevos_intentos = row["intentos"] + 1
        await db.execute(text(
            "UPDATE codigos_verificacion SET intentos = :i WHERE id = :id"
        ), {"i": nuevos_intentos, "id": row["id"]})
        await db.commit()
        restantes = 3 - nuevos_intentos
        raise HTTPException(status_code=400, detail=f"Codigo incorrecto. Te quedan {restantes} intento(s).")

    # Marcar codigo como usado
    await db.execute(text("UPDATE codigos_verificacion SET usado = TRUE WHERE id = :id"), {"id": row["id"]})

    # Buscar o crear estudiante
    # Buscar por correo primero, luego por cedula
    result2 = await db.execute(select(Estudiante).where(
        Estudiante.correo_institucional == data.correo_institucional
    ))
    estudiante = result2.scalar_one_or_none()
    if not estudiante:
        # Buscar por cedula
        result3 = await db.execute(select(Estudiante).where(
            Estudiante.cedula == data.cedula
        ))
        estudiante = result3.scalar_one_or_none()
    if not estudiante:
        estudiante = Estudiante(
            correo_institucional=data.correo_institucional,
            cedula=data.cedula,
            verificado=True
        )
        db.add(estudiante)
        await db.flush()
    else:
        # Actualizar cedula si cambio
        estudiante.correo_institucional = data.correo_institucional
        estudiante.cedula = data.cedula
        estudiante.verificado = True

    # Invalidar tokens anteriores
    tokens_ant = await db.execute(select(TokenSesion).where(
        TokenSesion.estudiante_id == estudiante.id,
        TokenSesion.expira_en > datetime.utcnow(),
        TokenSesion.usado == False
    ))
    for t in tokens_ant.scalars().all():
        t.usado = True

    # Crear nuevo token
    token_valor = generar_token()
    expira = datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)
    nuevo_token = TokenSesion(
        estudiante_id=estudiante.id,
        token=token_valor,
        expira_en=expira,
        ip_origen=request.client.host if request.client else None
    )
    db.add(nuevo_token)
    await db.commit()

    return TokenResponse(
        token=token_valor,
        expira_en=expira,
        estudiante_id=str(estudiante.id),
        mensaje="Verificacion exitosa. Token generado."
    )


@router.post("/verificar-token", summary="Verifica si un token es valido")
async def verificar_token(data: VerificarTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        estudiante, tok = await obtener_estudiante_por_token(data.token, db)
        return {"valido": True, "correo": estudiante.correo_institucional, "expira_en": tok.expira_en}
    except HTTPException:
        return {"valido": False}
