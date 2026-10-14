"""
Correo de error a soporte -- nivel ERROR (controlado). Usa la
plantilla real out/plantilla_error_controlado_correo.html (ver
plantilla_error.py).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config_reader import Configuracion
from core.notificaciones import construir_asunto, enviar_notificacion, NivelNotificacion
from proceso.reportes.plantilla_error import construir_cuerpo_error


def enviar_correo_soporte(
    config: Configuracion,
    mensaje: str,
    ruta_captura: Optional[Path],
    tiempo_inicio: datetime,
    logger,
) -> None:
    """
    Notifica un error controlado. `tiempo_inicio` se captura una vez
    al comienzo del proceso (ver main.py); tiempo_fin se toma en el
    momento de reportar el error.
    """
    tiempo_fin = datetime.now()
    nota = config.correo.obtener_nivel(NivelNotificacion.ERROR.value).nota
    asunto = construir_asunto(NivelNotificacion.ERROR, config.proceso.entorno, config.proceso.nombre_proceso, nota)
    cuerpo_html = construir_cuerpo_error(config, mensaje, tiempo_inicio, tiempo_fin, logger)

    enviar_notificacion(
        NivelNotificacion.ERROR,
        config.correo,
        asunto=asunto,
        cuerpo_html=cuerpo_html,
        logger=logger,
        ruta_adjunto=ruta_captura,
    )
