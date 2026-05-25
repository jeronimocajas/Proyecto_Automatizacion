# -*- coding: utf-8 -*-
import base64
import json
import time
import traceback
import httpx
from pathlib import Path
from core.config import settings

PROMPT_VALIDACION = """
Eres un agente validador del formulario F-BI-011 Solicitud de Auxilio Economico de CECAR.
Analiza el PDF y valida todos los campos con precision.

REGLAS:

1. DATOS PERSONALES (todos obligatorios):
Fecha solicitud, Nombres y Apellidos, Tipo identificacion (SOLO UNA opcion: CC, TI, CE),
Numero identificacion, Lugar y fecha nacimiento, Edad, Estado Civil (SOLO UNA opcion:
Soltero/Casado/Union libre/Divorciado/Viudo), Direccion, Barrio, Ciudad, Celular, Email.
- Semestre a cursar debe ser >= 2 (segundo semestre en adelante)

### 2. INFORMACION ACADEMICA (todos obligatorios)
- Programa Academico
- Facultad
- Promedio de nota semestral
- Promedio de notas acumulado
- Semestre a cursar

REGLAS DE PROMEDIO Y SEMESTRE segun el tipo de auxilio marcado en el formulario:

Si el tipo es AUXILIO ESPECIAL:
- OPCION A (requisitos completos): promedio acumulado >= 4.0 Y semestre >= 6. Aprobado.
- OPCION B (requisitos generales): promedio semestral >= 3.7 Y semestre >= 2. Aprobado.
- Si no cumple ninguna de las dos opciones: aprobado=false.
- Es decir: si el promedio semestral es >= 3.7 y el semestre es >= 2, SIEMPRE aprobar.

3. POBLACION INCLUSIVA: marcar EXACTAMENTE UNA opcion de:
Mujer Cabeza de Familia, Afrocolombiano, Indigena, Room, Victima/Desplazado, LGTBIQ+, Ninguna.
Cero opciones = ERROR. Dos o mas = ERROR.

4. DISCAPACIDAD: marcar EXACTAMENTE UNA opcion de:
Motora, Sensorial, Emocional, Cognitiva, Ninguna.
Cero opciones = ERROR. Dos o mas = ERROR.

5. TIPO DE APOYO SOCIOECONOMICO: marcar EXACTAMENTE UNA opcion de:
Auxilio Especial, Plan Padrino, Inclusion, Monitorias de Servicio, Monitoria Academica,
Deportes, Cultura, Escuelas de Formacion, Convenio, Trabajador CECAR, Otro.
Cero = ERROR. Dos o mas = ERROR.

### 6. INFORMACION FAMILIAR
Aplica esta regla segun el tipo de auxilio marcado EN EL FORMULARIO:

OBLIGATORIA (si falta algún campo, genera ERROR) cuando el tipo marcado es:
- Plan Padrino
- Inclusion
- Monitorias de Servicio

Campos obligatorios en esos casos: nombre del padre, ocupacion padre, empresa padre, direccion padre, telefono padre, nombre de la madre, ocupacion madre, empresa madre, direccion madre, telefono madre, lugar de residencia familiar, numero de personas en nucleo familiar, cuantas personas contribuyen.

OPCIONAL (nunca generes error por esta seccion) cuando el tipo marcado es:
- Auxilio Especial
- Monitoria Academica
- Deportes
- Cultura
- Escuelas de Formacion
- Convenio
- Trabajador CECAR
- Otro

7. INFORMACION SOCIOECONOMICA (todos obligatorios):
Ingreso mensual solicitante, Egreso mensual solicitante,
Ingreso mensual dependencia, Egreso mensual dependencia,
Credito ICETEX: Si o No (SOLO UNA opcion).

8. MOTIVO DE SOLICITUD: obligatorio, no puede estar vacio.

9. FIRMA DEL ESTUDIANTE: obligatoria.

RESPONDE SOLO CON JSON, sin texto adicional, sin bloques de codigo:

{
  "aprobado": true,
  "motivo_rechazo": null,
  "promedio_acumulado": 0.0,
  "promedio_valido": true,
  "campos_completos": true,
  "seleccion_unica_valida": true,
  "informacion_familiar_requerida": true,
  "campos_faltantes": [],
  "errores_seleccion": [],
  "datos_extraidos": {
    "nombres_apellidos": "",
    "identificacion_tipo": "",
    "identificacion_numero": "",
    "programa_academico": "",
    "facultad": "",
    "promedio_semestral": 0.0,
    "promedio_acumulado": 0.0,
    "semestre": 0,
    "tipo_auxilio_seleccionado": "",
    "poblacion_marcada": "",
    "discapacidad_marcada": "",
    "tiene_motivo": true,
    "tiene_firma": true,
    "informacion_familiar_completa": true
  },
  "observaciones": ""
}
"""

async def validar_formulario_pdf(ruta_pdf: str, tipo_auxilio: str) -> dict:
    start = time.time()

    pdf_path = Path(ruta_pdf)
    if not pdf_path.exists():
        return {
            "aprobado": False,
            "motivo_rechazo": "Archivo PDF no encontrado.",
            "error_sistema": True
        }

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("ascii")
    tipo_limpio = tipo_auxilio.encode("ascii", "ignore").decode("ascii")
    prompt_final = PROMPT_VALIDACION + f"\n\nEl sistema registra que el estudiante solicita: {tipo_limpio}. NO verifiques si el tipo marcado en el formulario coincide con este. Para la seccion de informacion familiar, aplica la regla del tipo que aparece marcado en el propio formulario."
    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt_final
                    }
                ],
            }
        ],
    }

    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                content=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        elapsed_ms = int((time.time() - start) * 1000)
        texto_respuesta = data["content"][0]["text"].strip()
        texto_respuesta = texto_respuesta.replace("```json", "").replace("```", "").strip()

        print("RESPUESTA IA:", texto_respuesta[:200])

        resultado = json.loads(texto_respuesta)
        resultado["tiempo_ms"] = elapsed_ms
        resultado["modelo"] = "claude-sonnet-4-20250514"
        return resultado

    except json.JSONDecodeError as e:
        print("ERROR JSON:", str(e))
        return {
            "aprobado": False,
            "motivo_rechazo": "Error al procesar respuesta del agente.",
            "error_sistema": True,
            "detalle_error": str(e)
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            "aprobado": False,
            "motivo_rechazo": "Error interno del agente.",
            "error_sistema": True,
            "detalle_error": str(e)
        }