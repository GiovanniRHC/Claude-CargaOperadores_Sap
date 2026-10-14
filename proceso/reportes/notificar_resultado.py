"""
Correo de finalización del proceso -- nivel EXITOSO_CON_REGISTRO /
EXITOSO_SIN_REGISTRO. Usa la plantilla real
out/plantilla_exitoso_correo.html (ver plantilla_exitoso.py).

*** ADAPTADO ***
La plantilla base solo tenía un nivel EXITOSO. Este proceso distingue
si hubo o no registros procesados (con_registros), porque Config.xlsx
trae dos filas separadas en la hoja Correo -- típicamente con
destinatarios/asunto distintos según si hay algo que revisar o no (ver
guía metodológica, sección 7.7: si no hay nada que reportar, no
mostrar una tabla vacía en el cuerpo -- eso se resuelve en
plantilla_exitoso.py/`resumen`, no aquí).
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config_reader import Configuracion
from core.notificaciones import construir_asunto, enviar_notificacion, NivelNotificacion
from proceso.reportes.plantilla_exitoso import construir_cuerpo_exitoso


def enviar_correo_resultado(
    config: Configuracion,
    resumen: str,
    con_registros: bool,
    tiempo_inicio: datetime,
    logger,
    ruta_adjunto: Optional[Path] = None,
    adjuntos_adicionales: Optional[list] = None,
) -> None:
    """
    `con_registros`: True si el proceso encontró/procesó al menos un
    registro en esta corrida -> nivel EXITOSO_CON_REGISTRO. False si
    corrió limpio pero no había nada que procesar -> EXITOSO_SIN_REGISTRO.
    """
    nivel = (
        NivelNotificacion.EXITOSO_CON_REGISTRO
        if con_registros
        else NivelNotificacion.EXITOSO_SIN_REGISTRO
    )
    tiempo_fin = datetime.now()
    nota = config.correo.obtener_nivel(nivel.value).nota
    asunto = construir_asunto(nivel, config.proceso.entorno, config.proceso.nombre_proceso, nota)
    cuerpo_html = construir_cuerpo_exitoso(config, resumen, tiempo_inicio, tiempo_fin, logger)

    enviar_notificacion(
        nivel,
        config.correo,
        asunto=asunto,
        cuerpo_html=cuerpo_html,
        logger=logger,
        ruta_adjunto=ruta_adjunto,
        adjuntos_adicionales=adjuntos_adicionales,
    )
