"""
Captura de pantalla para adjuntar a los correos de error, según el
estándar del robot: todo correo de notificación de error debe incluir
una captura de pantalla y el detalle técnico.

Requiere Pillow. Solo funciona con una sesión de escritorio interactiva
activa -- no funciona si el robot corre como servicio de Windows sin
sesión (esto es una limitación conocida de cualquier automatización de
UI, no algo específico de este código).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def tomar_captura_pantalla(carpeta_screenshot: Path, logger) -> Optional[Path]:
    """
    Toma una captura de la pantalla completa y la guarda en
    carpeta_screenshot. Retorna la ruta del archivo, o None si falla
    (por ejemplo, si Pillow no está instalado o no hay sesión de
    escritorio activa) -- nunca lanza excepción, para no interrumpir
    el flujo de manejo de errores que la está llamando.
    """
    try:
        from PIL import ImageGrab
    except ImportError:
        logger.warning("Pillow no está instalado; no se pudo tomar captura de pantalla.")
        return None

    nombre_archivo = f"Error_{datetime.now().strftime('%d%m%Y_%H%M%S')}.png"
    ruta_destino = carpeta_screenshot / nombre_archivo

    try:
        imagen = ImageGrab.grab()
        imagen.save(ruta_destino)
        return ruta_destino
    except Exception as error:
        logger.warning(f"No se pudo tomar la captura de pantalla: {error}")
        return None
