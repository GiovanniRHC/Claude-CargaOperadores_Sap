"""
Subflujos de manejo de errores, según el estándar del robot:

- ErrorControlado: errores conocidos del proceso (archivo no existe,
  contraseña cambiada, etc.). Se registra y se notifica a soporte.
- ErrorInesperado: cualquier caída no prevista durante la ejecución.
  Se registra con captura de pantalla y se notifica a soporte.

NOTA DE DISEÑO (pendiente de completar): el envío real del correo a
soporte se implementará en el módulo Reportes/Outlook, que todavía no
se ha construido. Por ahora estas funciones dejan la evidencia lista
(mensaje + captura) y llaman a un "notificador" inyectado, para que el
resto del robot no dependa de si el envío de correo ya existe o no.
"""

from pathlib import Path
from typing import Callable, Optional

NotificadorSoporte = Callable[[str, Optional[Path]], None]


class ErrorControlado(Exception):
    """Error conocido y esperado dentro del flujo del proceso."""


def manejar_error_controlado(
    logger,
    mensaje: str,
    notificar_soporte: Optional[NotificadorSoporte] = None,
    ruta_captura: Optional[Path] = None,
) -> None:
    logger.error(f"[ErrorControlado] {mensaje}")
    if notificar_soporte:
        notificar_soporte(mensaje, ruta_captura)


def manejar_error_inesperado(
    logger,
    excepcion: Exception,
    notificar_soporte: Optional[NotificadorSoporte] = None,
    ruta_captura: Optional[Path] = None,
) -> None:
    mensaje = f"[ErrorInesperado] {type(excepcion).__name__}: {excepcion}"
    logger.error(mensaje)
    if notificar_soporte:
        notificar_soporte(mensaje, ruta_captura)
