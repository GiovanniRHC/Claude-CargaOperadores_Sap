"""
Renderiza el correo EXITOSO, a partir de out/plantilla_exitoso_correo.html.

*** ADAPTAR AL PROYECTO NUEVO ***
Esta es una versión SIMPLE (sin tabla de detalle) -- si tu proceso
necesita mostrar una lista de registros procesados, agrega la lógica
de tabla dinámica siguiendo el patrón de tabla_resultados.py del
proyecto SSCO (extraer un renglón de ejemplo con regex, repetirlo por
cada fila real, reemplazar el original por el bloque generado).
"""

from datetime import datetime

from config.config_reader import Configuracion
from core.motor_plantillas import (
    formatear_duracion,
    formatear_fecha_hora_larga,
    renderizar_plantilla,
)

NOMBRE_ARCHIVO_PLANTILLA = "plantilla_exitoso_correo.html"


def construir_cuerpo_exitoso(
    config: Configuracion,
    resumen: str,
    tiempo_inicio: datetime,
    tiempo_fin: datetime,
    logger,
) -> str:
    """
    `resumen`: frase que describe lo que se procesó (reemplaza
    {Resumen de lo que se procesó} en la plantilla) -- ej. "Se
    procesaron 12 registros, todos correctamente."
    """
    reemplazos = {
        "Descripcion_Proceso": config.proceso.descripcion_proceso,
        "Unidad": config.proceso.unidad,
        "Resumen de lo que se procesó": resumen,
        "ObtenerFechaHoraInicioText": formatear_fecha_hora_larga(tiempo_inicio),
        "ObtenerFechaHoraFinText": formatear_fecha_hora_larga(tiempo_fin),
        "Duracion": formatear_duracion(tiempo_fin - tiempo_inicio),
    }

    nombre_salida = f"exitoso_{datetime.now().strftime('%d%m%Y_%H%M%S')}.html"
    return renderizar_plantilla(NOMBRE_ARCHIVO_PLANTILLA, reemplazos, nombre_salida, logger, prefijo_limpieza="exitoso_")
