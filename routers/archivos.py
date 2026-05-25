# -*- coding: utf-8 -*-
# routers/archivos.py
"""
Maneja la carga de archivos PDF, ejecuta la validación IA
y controla los intentos máximos (2).
"""
import hashlib
import shutil
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.database import get_db
from core.config import settings
from models.models import (Estudiante, TokenSesion, Solicitud, ArchivoSolicitud,
                            TipoAuxilio, ValidacionIA, LogCorreo)
from routers.auth import obtener_estudiante_por_token
from services.agente_validacion import validar_formulario_pdf
from services.correo import enviar_solicitud_aprobada, enviar_notificacion_rechazo

router = APIRouter()

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

# -- Endpoint principal ----------------------------------------
@router.post("/cargar", summary="Cargar documentos PDF y ejecutar validación IA")
async def cargar_documentos(
    token:          str        = Form(...),
    tipo_auxilio_codigo: str   = Form(...),
    formulario_pdf: UploadFile = File(..., description="Formulario F-BI-011 en PDF"),
    carta_pdf: UploadFile = File(None, description="Carta de solicitud en PDF (opcional)"),
    db: AsyncSession = Depends(get_db)
):
    
    print("========== DEBUG CARGA ==========")
    print("TIPO AUXILIO:", tipo_auxilio_codigo)
    print("TOKEN:", token)
    print("CONTENT TYPE:", formulario_pdf.content_type)
    print("FILENAME:", formulario_pdf.filename)
    print("UPLOAD PATH:", UPLOAD_PATH)
    print("=================================")
    
    # ── 0. Verificar convocatoria activa ─────────────────────
    conv_result = await db.execute(text("SELECT id FROM convocatorias WHERE activa = TRUE LIMIT 1"))
    if not conv_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No hay una convocatoria activa en este momento. Consulta las fechas de la proxima convocatoria."
        )

    # -- 1. Validar token -------------------------------------
    print(">> PASO 1: validando token...")
    estudiante, tok = await obtener_estudiante_por_token(token, db)
    print(f">> PASO 1 OK: {estudiante.id}")

    # -- 2. Verificar tipo de auxilio -------------------------
    print(">> PASO 2: verificando tipo auxilio...")
    result = await db.execute(
        select(TipoAuxilio).where(
            TipoAuxilio.codigo == tipo_auxilio_codigo.upper(),
            TipoAuxilio.activo == True
        )
    )
    tipo_auxilio = result.scalar_one_or_none()
    print(f">> PASO 2 RESULTADO: {tipo_auxilio}")
    if not tipo_auxilio:
        raise HTTPException(status_code=400, detail="Tipo de auxilio no válido.")
    print(f">> PASO 2 OK: {tipo_auxilio.nombre}")

    # -- 3. Verificar que no tenga solicitud aprobada/enviada -
    print(">> PASO 3: verificando solicitud existente...")
    result = await db.execute(
        select(Solicitud).where(
            Solicitud.estudiante_id == estudiante.id,
            Solicitud.estado.in_(["APROBADO", "ENVIADO"])
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Ya tienes una solicitud aprobada o enviada. No puedes presentar otra."
        )

    # -- 4. Buscar solicitud pendiente existente (para intentos) -
    result = await db.execute(
        select(Solicitud).where(
            Solicitud.estudiante_id == estudiante.id,
            Solicitud.estado.in_(["PENDIENTE", "ERROR_VALIDACION"])
        )
    )
    solicitud = result.scalar_one_or_none()

    if solicitud:
        if solicitud.intentos >= settings.MAX_INTENTOS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Has alcanzado el máximo de {settings.MAX_INTENTOS} intentos. "
                    "Tu solicitud ha sido bloqueada. Contacta a Bienestar Institucional."
                )
            )
        # Verificar que sea para el mismo tipo de auxilio
        if solicitud.tipo_auxilio_id != tipo_auxilio.id:
            raise HTTPException(
                status_code=400,
                detail="No puedes cambiar el tipo de auxilio entre intentos."
            )
        intento_actual = solicitud.intentos + 1
    else:
        # Primera vez - crear solicitud
        solicitud = Solicitud(
            estudiante_id=estudiante.id,
            token_id=tok.id,
            tipo_auxilio_id=tipo_auxilio.id,
            estado="PENDIENTE",
            intentos=0,
            correo_destino=settings.CORREO_DESTINO_BIENESTAR
        )
        db.add(solicitud)
        await db.flush()
        intento_actual = 1

    # -- 5. Validar tamaño del archivo ------------------------
    contenido = await formulario_pdf.read()
# DEBUG TEMPORAL
    print(f"CONTENT TYPE EXACTO: '{formulario_pdf.content_type}'")
    print(f"CONTENT TYPE REPR: {repr(formulario_pdf.content_type)}")

    if len(contenido) > MAX_SIZE_BYTES:
     ...
    if len(contenido) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {settings.MAX_FILE_SIZE_MB}MB."
        )

    if formulario_pdf.content_type and "pdf" not in formulario_pdf.content_type.lower():
        raise HTTPException(
        status_code=400,
        detail="Solo se aceptan archivos PDF."
    )

    # -- 6. Guardar archivo -----------------------------------
    nombre_unico = f"{uuid.uuid4().hex}_intento{intento_actual}_{formulario_pdf.filename}"
    carpeta_solicitud = UPLOAD_PATH / str(solicitud.id)
    carpeta_solicitud.mkdir(parents=True, exist_ok=True)
    ruta_guardado = carpeta_solicitud / nombre_unico

    with open(ruta_guardado, "wb") as f:
        f.write(contenido)

    hash_archivo = hashlib.sha256(contenido).hexdigest()

    archivo_db = ArchivoSolicitud(
        solicitud_id=solicitud.id,
        nombre_original=formulario_pdf.filename,
        nombre_almacenado=nombre_unico,
        ruta_almacenamiento=str(ruta_guardado),
        tipo_mime=formulario_pdf.content_type,
        tamanio_bytes=len(contenido),
        hash_sha256=hash_archivo,
        intento_numero=intento_actual
    )
    db.add(archivo_db)

    # Guardar carta si fue enviada
    ruta_carta = None
    if carta_pdf and carta_pdf.filename:
        contenido_carta = await carta_pdf.read()
        if len(contenido_carta) > 0:
            nombre_carta = f"{uuid.uuid4().hex}_carta_{carta_pdf.filename}"
            ruta_carta = carpeta_solicitud / nombre_carta
            with open(ruta_carta, "wb") as f:
                f.write(contenido_carta)
            carta_db = ArchivoSolicitud(
                solicitud_id=solicitud.id,
                nombre_original=carta_pdf.filename,
                nombre_almacenado=nombre_carta,
                ruta_almacenamiento=str(ruta_carta),
                tipo_mime=carta_pdf.content_type,
                tamanio_bytes=len(contenido_carta),
                hash_sha256=hashlib.sha256(contenido_carta).hexdigest(),
                intento_numero=intento_actual
            )
            db.add(carta_db)

    # -- 7. Ejecutar agente IA --------------------------------
    solicitud.intentos = intento_actual
    solicitud.estado = "VALIDANDO"
    await db.flush()

    print("LLAMANDO A IA CON:", str(ruta_guardado), tipo_auxilio.nombre)
    resultado_ia = await validar_formulario_pdf(str(ruta_guardado), tipo_auxilio.nombre)
    print("RESULTADO IA:", resultado_ia)

    # Guardar log de validación
    validacion_log = ValidacionIA(
        solicitud_id=solicitud.id,
        intento_numero=intento_actual,
        respuesta_ia=resultado_ia,
        resultado="APROBADO" if resultado_ia.get("aprobado") else "RECHAZADO",
        campos_invalidos=resultado_ia.get("campos_faltantes", []),
        tiempo_ms=resultado_ia.get("tiempo_ms")
    )
    db.add(validacion_log)

    # -- 8. Procesar resultado --------------------------------
    if resultado_ia.get("aprobado"):
        # Actualizar datos de la solicitud con lo extraído por IA
        datos = resultado_ia.get("datos_extraidos", {})
        solicitud.promedio_acumulado = datos.get("promedio_acumulado")
        solicitud.resultado_validacion = resultado_ia
        solicitud.estado = "APROBADO"

        # Enviar correo a Bienestar Institucional
        datos_est = {
            "nombres_apellidos": datos.get("nombres_apellidos", estudiante.correo_institucional),
            "cedula": estudiante.cedula,
            "correo": estudiante.correo_institucional,
            "programa": datos.get("programa_academico", ""),
            "promedio_acumulado": datos.get("promedio_acumulado", "")
        }

        correo_ok = enviar_solicitud_aprobada(
            destinatario=solicitud.correo_destino,
            datos_estudiante=datos_est,
            tipo_auxilio=tipo_auxilio.nombre,
            archivos_adjuntos=[str(ruta_guardado)] + ([str(ruta_carta)] if ruta_carta else [])
        )

        solicitud.correo_enviado = correo_ok
        solicitud.fecha_envio_correo = datetime.utcnow() if correo_ok else None
        solicitud.estado = "ENVIADO" if correo_ok else "APROBADO"

        log_correo = LogCorreo(
            solicitud_id=solicitud.id,
            destinatario=solicitud.correo_destino,
            asunto=f"Solicitud {tipo_auxilio.nombre} - {datos_est['nombres_apellidos']}",
            estado="ENVIADO" if correo_ok else "ERROR",
        )
        db.add(log_correo)
        await db.commit()

        return {
            "estado": "APROBADO",
            "mensaje": (
                "[OK] Tu solicitud fue validada exitosamente y enviada a Bienestar Institucional. "
                "Recibirás respuesta en los próximos días hábiles."
            ),
            "correo_enviado": correo_ok,
            "intento": intento_actual
        }

    else:
        # Solicitud rechazada por validación IA
        campos_faltantes = resultado_ia.get("campos_faltantes", [])
        errores_seleccion = resultado_ia.get("errores_seleccion", [])
        todos_errores = campos_faltantes + errores_seleccion
        observaciones = resultado_ia.get("observaciones", "")
        motivo = resultado_ia.get("motivo_rechazo", "El formulario no cumple con los requisitos.")

        solicitud.estado = "ERROR_VALIDACION"
        solicitud.campos_faltantes = todos_errores
        solicitud.observaciones_ia = observaciones
        solicitud.resultado_validacion = resultado_ia

        intentos_restantes = settings.MAX_INTENTOS - intento_actual

        # Notificar al estudiante por correo
        enviar_notificacion_rechazo(
            correo_estudiante=estudiante.correo_institucional,
            tipo_auxilio=tipo_auxilio.nombre,
            campos_faltantes=todos_errores,
            intentos_restantes=intentos_restantes,
            observaciones=observaciones
        )

        await db.commit()

        if intentos_restantes <= 0:
            solicitud.estado = "RECHAZADO"
            await db.commit()
            raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "estado": "BLOQUEADO",
                            "mensaje": "Has agotado todos los intentos disponibles. Contacta directamente a Bienestar Institucional.",
                            "motivo": motivo,
                            "campos_con_problemas": todos_errores
                        }
                    )

      # Construir mensaje explicativo según el motivo de rechazo
        resultado_datos = resultado_ia.get("datos_extraidos", {})
        tipo_en_formulario = resultado_datos.get("tipo_auxilio_seleccionado", "")
        promedio_acumulado = resultado_datos.get("promedio_acumulado", 0)
        promedio_semestral = resultado_datos.get("promedio_semestral", 0)
        semestre = resultado_datos.get("semestre", 0)

        if "AUXILIO ESPECIAL" in tipo_en_formulario.upper() or tipo_auxilio.nombre.upper() == "AUXILIO ESPECIAL":
            if promedio_semestral and float(promedio_semestral) < 3.7:
                motivo = f"Para Auxilio Especial se requiere promedio semestral minimo de 3.7. Tu promedio semestral es {promedio_semestral}."
            elif semestre and int(semestre) < 2:
                motivo = f"Para Auxilio Especial debes estar cursando minimo segundo semestre. Actualmente estas en semestre {semestre}."
        elif "PLAN PADRINO" in tipo_en_formulario.upper() or tipo_auxilio.nombre.upper() == "PLAN PADRINO":
            if promedio_semestral and float(promedio_semestral) < 3.7:
                motivo = f"Para Plan Padrino se requiere promedio semestral minimo de 3.7. Tu promedio semestral es {promedio_semestral}."
        else:
            if promedio_semestral and float(promedio_semestral) < 3.7:
                motivo = f"Se requiere promedio semestral minimo de 3.7. Tu promedio semestral es {promedio_semestral}."
            elif promedio_acumulado and float(promedio_acumulado) < 3.7:
                motivo = f"Se requiere promedio acumulado minimo de 3.7. Tu promedio acumulado es {promedio_acumulado}."

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "estado": "ERROR_VALIDACION",
                "mensaje": f"El formulario tiene errores. Tienes {intentos_restantes} intento(s) restante(s).",
                "motivo": motivo,
                "campos_con_problemas": todos_errores,
                "intentos_restantes": intentos_restantes,
                "intento_actual": intento_actual
            }
        )


@router.get("/estado/{token}", summary="Consultar estado de la solicitud")
async def estado_solicitud(token: str, db: AsyncSession = Depends(get_db)):
    estudiante, _ = await obtener_estudiante_por_token(token, db)

    result = await db.execute(
        select(Solicitud).where(
            Solicitud.estudiante_id == estudiante.id
        ).order_by(Solicitud.creado_en.desc())
    )
    solicitud = result.scalar_one_or_none()

    if not solicitud:
        return {"estado": "SIN_SOLICITUD", "mensaje": "No tienes solicitudes registradas."}

    return {
        "estado": solicitud.estado,
        "intentos_usados": solicitud.intentos,
        "intentos_restantes": max(0, settings.MAX_INTENTOS - solicitud.intentos),
        "correo_enviado": solicitud.correo_enviado,
        "campos_con_problemas": solicitud.campos_faltantes or [],
        "creado_en": solicitud.creado_en
    }
