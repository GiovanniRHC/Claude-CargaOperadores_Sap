"""
Envío de correos vía SMTP (Microsoft 365) -- reemplaza el envío por
Outlook COM.

Motivo del cambio: Outlook tiene un mecanismo de seguridad nativo
("Object Model Guard") que muestra un popup cada vez que un programa
externo intenta enviar un correo en nombre del usuario. Ese popup
bloquea el canal por completo hasta que alguien hace clic manualmente
-- el mismo patrón de bloqueo que ya resolvimos con el popup de
"Seguridad SAP GUI", pero esta vez en Outlook. SMTP directo no pasa por
Outlook en absoluto, así que ese popup no puede aparecer.

Servidor: smtp.office365.com, puerto 587 (STARTTLS).

RIESGO CONOCIDO: Microsoft 365 deshabilita "SMTP AUTH básico" por
defecto a nivel de organización desde 2022. Si el envío falla con un
error de autenticación, no es un bug de este código -- hay que pedir a
TI que habilite SMTP AUTH para esta cuenta específica
(notificaciones@empresa-demo.com), o generar una contraseña de
aplicación si más adelante se activa doble factor.
"""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable, Optional

from config.config_reader import ConfiguracionCorreo

SERVIDOR_SMTP = "smtp.office365.com"
PUERTO_SMTP = 587
SEGUNDOS_TIMEOUT_SMTP = 30


class ErrorEnvioCorreo(Exception):
    """Error controlado al enviar un correo por SMTP."""


def _construir_mensaje(
    config_correo: ConfiguracionCorreo,
    destinatarios: Iterable[str],
    asunto: str,
    cuerpo_html: str,
    copia: Iterable[str],
    rutas_adjuntos: Iterable[Path],
) -> MIMEMultipart:
    mensaje = MIMEMultipart()
    mensaje["From"] = config_correo.principal
    mensaje["To"] = ", ".join(destinatarios)
    if copia:
        mensaje["Cc"] = ", ".join(copia)
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo_html, "html"))

    for ruta_adjunto in rutas_adjuntos:
        if ruta_adjunto is None or not Path(ruta_adjunto).exists():
            continue
        with open(ruta_adjunto, "rb") as archivo:
            adjunto = MIMEApplication(archivo.read(), Name=Path(ruta_adjunto).name)
        adjunto["Content-Disposition"] = f'attachment; filename="{Path(ruta_adjunto).name}"'
        mensaje.attach(adjunto)

    return mensaje


def enviar_correo_smtp(
    config_correo: ConfiguracionCorreo,
    destinatarios: Iterable[str],
    asunto: str,
    cuerpo_html: str,
    logger,
    copia: Iterable[str] = (),
    ruta_adjunto: Optional[Path] = None,
    adjuntos_adicionales: Optional[Iterable[Path]] = None,
) -> None:
    """
    Envía un correo vía SMTP (Microsoft 365), usando las credenciales
    de Config.xlsx (hoja Correo: Principal, Contrasena).

    `ruta_adjunto` sigue existiendo por compatibilidad (un solo
    adjunto, como antes). `adjuntos_adicionales` permite sumar más
    archivos sin afectar a los llamadores que ya usaban ruta_adjunto.

    Lanza ErrorEnvioCorreo si falla -- cada llamador decide si eso
    detiene el proceso o solo se registra como advertencia.
    """
    destinatarios = list(destinatarios)
    copia = list(copia)

    rutas_adjuntos = []
    if ruta_adjunto is not None:
        rutas_adjuntos.append(ruta_adjunto)
    if adjuntos_adicionales:
        rutas_adjuntos.extend(adjuntos_adicionales)

    mensaje = _construir_mensaje(config_correo, destinatarios, asunto, cuerpo_html, copia, rutas_adjuntos)
    todos_los_destinatarios = destinatarios + copia

    try:
        with smtplib.SMTP(SERVIDOR_SMTP, PUERTO_SMTP, timeout=SEGUNDOS_TIMEOUT_SMTP) as servidor:
            servidor.starttls()
            servidor.login(config_correo.principal, config_correo.contrasena)
            servidor.sendmail(config_correo.principal, todos_los_destinatarios, mensaje.as_string())
        logger.success(f"Correo enviado a: {', '.join(todos_los_destinatarios)}")
    except smtplib.SMTPAuthenticationError as error:
        raise ErrorEnvioCorreo(
            "Falló la autenticación SMTP. Si Microsoft 365 tiene deshabilitado "
            f"'SMTP AUTH básico' para esta cuenta, pedir a TI que lo habilite. Detalle: {error}"
        ) from error
    except Exception as error:
        raise ErrorEnvioCorreo(f"No se pudo enviar el correo vía SMTP: {error}") from error
