# -*- coding: utf-8 -*-
# services/correo.py
import resend
from core.config import settings

def _init():
    resend.api_key = settings.RESEND_API_KEY

def enviar_codigo_verificacion(correo_destino: str, codigo: str) -> bool:
    _init()
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "jeronimocajas5930@gmail.com",
            "subject": "[CECAR] Codigo de verificacion - Auxilios Economicos",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
                <div style="background:#1a1a1a;padding:20px;text-align:center;">
                    <h2 style="color:#fff;margin:0;">Verificacion de Identidad</h2>
                    <p style="color:#aaa;margin:5px 0;">Bienestar Institucional - CECAR</p>
                </div>
                <div style="padding:30px;text-align:center;">
                    <p style="font-size:15px;">Tu codigo de verificacion para acceder al sistema de auxilios es:</p>
                    <div style="background:#e8f5e2;border:2px solid #60ad45;border-radius:12px;padding:24px;margin:24px 0;display:inline-block;">
                        <span style="font-size:42px;font-weight:900;letter-spacing:12px;color:#4a8f33;">{codigo}</span>
                    </div>
                    <p style="color:#666;font-size:13px;">Este codigo expira en <strong>10 minutos</strong>.</p>
                    <p style="color:#666;font-size:13px;">Si no solicitaste este codigo, ignora este mensaje.</p>
                </div>
            </div>
            """
        })
        print(f"CODIGO ENVIADO OK a {correo_destino}")
        return True
    except Exception as e:
        print(f"ERROR RESEND CODIGO: {e}")
        return False


def enviar_solicitud_aprobada(
    destinatario: str,
    datos_estudiante: dict,
    tipo_auxilio: str,
    archivos_adjuntos: list[str]
) -> bool:
    _init()
    try:
        adjuntos_count = len(archivos_adjuntos)
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": destinatario,
            "subject": (
                f"[AUXILIO {tipo_auxilio.upper()}] Solicitud de "
                f"{datos_estudiante.get('nombres_apellidos', 'Estudiante')} - "
                f"Cedula {datos_estudiante.get('cedula', '')}"
            ),
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
                <div style="background:#1a1a1a;padding:20px;text-align:center;">
                    <h2 style="color:#fff;margin:0;">Solicitud de Auxilio Economico</h2>
                    <p style="color:#aaa;margin:5px 0;">Bienestar Institucional - CECAR</p>
                </div>
                <div style="padding:30px;">
                    <p>Estimado equipo de Bienestar Institucional,</p>
                    <p>Se ha recibido y <strong>validado automaticamente</strong> una nueva solicitud de auxilio economico.</p>
                    <table style="width:100%;border-collapse:collapse;margin:20px 0;">
                        <tr style="background:#e8f5e2;">
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Estudiante</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;">{datos_estudiante.get('nombres_apellidos', '-')}</td>
                        </tr>
                        <tr>
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Cedula</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;">{datos_estudiante.get('cedula', '-')}</td>
                        </tr>
                        <tr style="background:#e8f5e2;">
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Correo institucional</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;">{datos_estudiante.get('correo', '-')}</td>
                        </tr>
                        <tr>
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Programa academico</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;">{datos_estudiante.get('programa', '-')}</td>
                        </tr>
                        <tr style="background:#e8f5e2;">
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Tipo de auxilio</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;"><strong>{tipo_auxilio}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding:10px;border:1px solid #ddd;"><strong>Promedio acumulado</strong></td>
                            <td style="padding:10px;border:1px solid #ddd;">{datos_estudiante.get('promedio_acumulado', '-')}</td>
                        </tr>
                    </table>
                    <p style="background:#e8f5e2;border-left:4px solid #60ad45;padding:10px;border-radius:4px;">
                        [OK] Documentos validados automaticamente por el agente IA.
                        Se adjuntan {adjuntos_count} archivo(s) a este correo.
                    </p>
                    <p style="font-size:12px;color:#888;margin-top:30px;">
                        Este correo fue generado automaticamente por el Sistema de Auxilios Economicos de CECAR.<br>
                        No responder a este mensaje.
                    </p>
                </div>
            </div>
            """
        })
        print(f"CORREO APROBADO OK a {destinatario}")
        return True
    except Exception as e:
        print(f"ERROR RESEND APROBADO: {e}")
        return False


def enviar_notificacion_rechazo(
    correo_estudiante: str,
    tipo_auxilio: str,
    campos_faltantes: list[str],
    intentos_restantes: int,
    observaciones: str = ""
) -> bool:
    _init()
    try:
        lista_errores = "".join([f"<li>{c}</li>" for c in campos_faltantes])
        obs_html = f"<p><em>{observaciones}</em></p>" if observaciones else ""
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": correo_estudiante,
            "subject": f"[CECAR] Tu solicitud de {tipo_auxilio} requiere correcciones",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
                <div style="background:#1a1a1a;padding:20px;text-align:center;">
                    <h2 style="color:#fff;margin:0;">Solicitud de Auxilio Economico</h2>
                    <p style="color:#aaa;margin:5px 0;">Bienestar Institucional - CECAR</p>
                </div>
                <div style="padding:30px;">
                    <p>Estimado/a estudiante,</p>
                    <p>Tu solicitud de <strong>{tipo_auxilio}</strong> fue revisada y encontramos los siguientes problemas:</p>
                    <div style="background:#fff3e0;border-left:4px solid #ff9900;padding:15px;border-radius:4px;margin:20px 0;">
                        <strong>[!] Campos con problemas:</strong>
                        <ul style="margin:10px 0;">{lista_errores}</ul>
                        {obs_html}
                    </div>
                    <p style="background:#e8f5e2;border-left:4px solid #60ad45;padding:10px;border-radius:4px;">
                        Tienes <strong>{intentos_restantes} intento(s)</strong> restante(s) para cargar tus documentos corregidos.
                    </p>
                    <p>Por favor, corrige los documentos y vuelve a cargarlos en el sistema.</p>
                    <p style="font-size:12px;color:#888;margin-top:30px;">
                        Sistema de Auxilios Economicos - CECAR<br>
                        Este es un correo automatico, no responder.
                    </p>
                </div>
            </div>
            """
        })
        print(f"CORREO RECHAZO OK a {correo_estudiante}")
        return True
    except Exception as e:
        print(f"ERROR RESEND RECHAZO: {e}")
        return False
