"""
Correo de error INESPERADO a soporte -- nivel ERROR_INESPERADO. Usa la
plantilla real out/plantilla_error_inesperado_correo.html (ver
plantilla_error_inesperado.py).

Distinto del error CONTROLADO (notificar_soporte.py): este es para
excepciones que el código no anticipó con un tipo propio (ver
core/manejo_errores.py -> manejar_error_inesperado).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config_reader import Configuracion
from core.notificaciones import construir_asunto, enviar_notificacion, NivelNotificacion
from proceso.reportes.plantilla_error_inesperado import construir_cuerpo_error_inesperado


def enviar_correo_error_inesperado(
    config: Configuracion,
    mensaje: str,
    ruta_captura: Optional[Path],
    tiempo_inicio: datetime,
    logger,
) -> None:
    tiempo_fin = datetime.now()
    nota = config.correo.obtener_nivel(NivelNotificacion.ERROR_INESPERADO.value).nota
    asunto = construir_asunto(
        NivelNotificacion.ERROR_INESPERADO, config.proceso.entorno, config.proceso.nombre_proceso, nota
    )
    cuerpo_html = construir_cuerpo_error_inesperado(config, mensaje, tiempo_inicio, tiempo_fin, logger)

    enviar_notificacion(
        NivelNotificacion.ERROR_INESPERADO,
        config.correo,
        asunto=asunto,
        cuerpo_html=cuerpo_html,
        logger=logger,
        ruta_adjunto=ruta_captura,
    )
