# -*- coding: utf-8 -*-
# routers/convocatorias.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from core.database import get_db
from core.config import settings
from sqlalchemy import text

router = APIRouter()

# ── Modelos ──────────────────────────────────────────────────
class AdminLogin(BaseModel):
    usuario: str
    password: str

class ConvocatoriaCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date

class ConvocatoriaUpdate(BaseModel):
    activa: bool

# ── Auth ──────────────────────────────────────────────────────
def verificar_admin(usuario: str, password: str):
    if usuario != settings.ADMIN_USUARIO or password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administrador incorrectas."
        )

# ── Endpoints públicos ────────────────────────────────────────
@router.get("/estado", summary="Estado actual de la convocatoria")
async def estado_convocatoria(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT id, nombre, fecha_inicio, fecha_fin, activa
        FROM convocatorias
        WHERE activa = TRUE
        ORDER BY fecha_inicio DESC
        LIMIT 1
    """))
    activa = result.mappings().fetchone()

    result2 = await db.execute(text("""
        SELECT id, nombre, fecha_inicio, fecha_fin
        FROM convocatorias
        WHERE activa = FALSE AND fecha_inicio > CURRENT_DATE
        ORDER BY fecha_inicio ASC
        LIMIT 1
    """))
    proxima = result2.mappings().fetchone()

    return {
        "convocatoria_abierta": activa is not None,
        "convocatoria_activa": dict(activa) if activa else None,
        "proxima_convocatoria": dict(proxima) if proxima else None
    }

# ── Endpoints de administración ───────────────────────────────
@router.post("/admin/login", summary="Login del administrador")
async def admin_login(data: AdminLogin):
    verificar_admin(data.usuario, data.password)
    return {"autenticado": True, "mensaje": "Acceso concedido al panel de administracion."}

@router.get("/admin/listar", summary="Listar todas las convocatorias")
async def listar_convocatorias(
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    result = await db.execute(text("""
        SELECT id, nombre, fecha_inicio, fecha_fin, activa, creado_en
        FROM convocatorias
        ORDER BY fecha_inicio DESC
    """))
    rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.post("/admin/crear", summary="Crear nueva convocatoria")
async def crear_convocatoria(
    data: ConvocatoriaCreate,
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    if data.fecha_fin <= data.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de cierre debe ser posterior a la de apertura.")
    await db.execute(text("""
        INSERT INTO convocatorias (nombre, fecha_inicio, fecha_fin, activa)
        VALUES (:nombre, :inicio, :fin, FALSE)
    """), {"nombre": data.nombre, "inicio": data.fecha_inicio, "fin": data.fecha_fin})
    await db.commit()
    return {"mensaje": "Convocatoria creada exitosamente."}

@router.put("/admin/activar/{id}", summary="Activar una convocatoria")
async def activar_convocatoria(
    id: int,
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    await db.execute(text("UPDATE convocatorias SET activa = FALSE"))
    await db.execute(text("""
        UPDATE convocatorias SET activa = TRUE
        WHERE id = :id
    """), {"id": id})
    await db.commit()
    return {"mensaje": f"Convocatoria {id} activada. Las demas fueron desactivadas."}

@router.put("/admin/desactivar/{id}", summary="Desactivar una convocatoria")
async def desactivar_convocatoria(
    id: int,
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    await db.execute(text("""
        UPDATE convocatorias SET activa = FALSE
        WHERE id = :id
    """), {"id": id})
    await db.commit()
    return {"mensaje": f"Convocatoria {id} desactivada."}

@router.delete("/admin/eliminar/{id}", summary="Eliminar una convocatoria")
async def eliminar_convocatoria(
    id: int,
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    await db.execute(text("DELETE FROM convocatorias WHERE id = :id"), {"id": id})
    await db.commit()
    return {"mensaje": f"Convocatoria {id} eliminada."}

@router.get("/admin/estudiantes", summary="Listar estudiantes con solicitudes")
async def listar_estudiantes(
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    result = await db.execute(text("""
        SELECT 
            e.id, e.correo_institucional, e.cedula,
            s.id as solicitud_id, s.estado, s.intentos,
            s.tipo_auxilio_id, ta.nombre as tipo_auxilio,
            s.creado_en
        FROM estudiantes e
        LEFT JOIN solicitudes s ON s.estudiante_id = e.id
        LEFT JOIN tipos_auxilio ta ON ta.id = s.tipo_auxilio_id
        ORDER BY s.creado_en DESC NULLS LAST
    """))
    rows = result.mappings().fetchall()
    return [dict(r) for r in rows]

@router.put("/admin/reiniciar-intentos/{solicitud_id}", summary="Reiniciar intentos de una solicitud")
async def reiniciar_intentos(
    solicitud_id: str,
    usuario: str, password: str,
    db: AsyncSession = Depends(get_db)
):
    verificar_admin(usuario, password)
    await db.execute(text("""
        UPDATE solicitudes 
        SET intentos = 0, estado = 'PENDIENTE', 
            campos_faltantes = NULL, observaciones_ia = NULL,
            resultado_validacion = NULL
        WHERE id = :id
    """), {"id": solicitud_id})
    await db.commit()
    return {"mensaje": "Intentos reiniciados exitosamente. El estudiante puede volver a cargar sus documentos."}
