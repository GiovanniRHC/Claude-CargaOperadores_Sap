"""
Renderiza el correo de ERROR INESPERADO, a partir de
out/plantilla_error_inesperado_correo.html.

Distinto del error CONTROLADO (plantilla_error.py): este es para
excepciones que el código no anticipó con un tipo propio (ver
core/manejo_errores.py -> manejar_error_inesperado).
"""

from datetime import datetime

from config.config_reader import Configuracion
from core.motor_plantillas import formatear_duracion, formatear_fecha_hora_larga, renderizar_plantilla

NOMBRE_ARCHIVO_PLANTILLA = "plantilla_error_inesperado_correo.html"


def construir_cuerpo_error_inesperado(
    config: Configuracion,
    mensaje_error: str,
    tiempo_inicio: datetime,
    tiempo_fin: datetime,
    logger,
) -> str:
    reemplazos = {
        "Descripcion_Proceso": config.proceso.descripcion_proceso,
        "Unidad": config.proceso.unidad,
        "Describe el error, por qué falló": mensaje_error,
        "ObtenerFechaHoraInicioText": formatear_fecha_hora_larga(tiempo_inicio),
        "ObtenerFechaHoraFinText": formatear_fecha_hora_larga(tiempo_fin),
        "Duracion": formatear_duracion(tiempo_fin - tiempo_inicio),
    }

    nombre_salida = f"error_inesperado_{datetime.now().strftime('%d%m%Y_%H%M%S')}.html"
    return renderizar_plantilla(
        NOMBRE_ARCHIVO_PLANTILLA, reemplazos, nombre_salida, logger, prefijo_limpieza="error_inesperado_"
    )
