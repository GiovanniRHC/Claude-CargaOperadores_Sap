"""Renderiza el correo ADVERTENCIA, a partir de out/plantilla_advertencia_correo.html."""

from datetime import datetime

from config.config_reader import Configuracion
from core.motor_plantillas import formatear_duracion, formatear_fecha_hora_larga, renderizar_plantilla

NOMBRE_ARCHIVO_PLANTILLA = "plantilla_advertencia_correo.html"


def construir_cuerpo_advertencia(
    config: Configuracion,
    resumen: str,
    tiempo_inicio: datetime,
    tiempo_fin: datetime,
    logger,
) -> str:
    """
    `resumen`: frase que describe qué quedó pendiente o requiere
    revisión (reemplaza {Resumen de qué quedó pendiente o requiere revisión}).
    """
    reemplazos = {
        "Descripcion_Proceso": config.proceso.descripcion_proceso,
        "Unidad": config.proceso.unidad,
        "Resumen de qué quedó pendiente o requiere revisión": resumen,
        "ObtenerFechaHoraInicioText": formatear_fecha_hora_larga(tiempo_inicio),
        "ObtenerFechaHoraFinText": formatear_fecha_hora_larga(tiempo_fin),
        "Duracion": formatear_duracion(tiempo_fin - tiempo_inicio),
    }

    nombre_salida = f"advertencia_{datetime.now().strftime('%d%m%Y_%H%M%S')}.html"
    return renderizar_plantilla(NOMBRE_ARCHIVO_PLANTILLA, reemplazos, nombre_salida, logger, prefijo_limpieza="advertencia_")
