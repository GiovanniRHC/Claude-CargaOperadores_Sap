"""
Correo de finalización con ADVERTENCIA -- nivel ADVERTENCIA. Usa la
plantilla real out/plantilla_advertencia_correo.html (ver
plantilla_advertencia.py).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config_reader import Configuracion
from core.notificaciones import construir_asunto, enviar_notificacion, NivelNotificacion
from proceso.reportes.plantilla_advertencia import construir_cuerpo_advertencia


def enviar_correo_advertencia(
    config: Configuracion,
    resumen: str,
    tiempo_inicio: datetime,
    logger,
    ruta_adjunto: Optional[Path] = None,
    adjuntos_adicionales: Optional[list] = None,
) -> None:
    tiempo_fin = datetime.now()
    nota = config.correo.obtener_nivel(NivelNotificacion.ADVERTENCIA.value).nota
    asunto = construir_asunto(NivelNotificacion.ADVERTENCIA, config.proceso.entorno, config.proceso.nombre_proceso, nota)
    cuerpo_html = construir_cuerpo_advertencia(config, resumen, tiempo_inicio, tiempo_fin, logger)

    enviar_notificacion(
        NivelNotificacion.ADVERTENCIA,
        config.correo,
        asunto=asunto,
        cuerpo_html=cuerpo_html,
        logger=logger,
        ruta_adjunto=ruta_adjunto,
        adjuntos_adicionales=adjuntos_adicionales,
    )
