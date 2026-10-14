"""
Renderiza el correo INFO (inicio de proceso), a partir de
out/plantilla_info_inicio_proceso_correo.html.

Caso especial: el marcador {Aqui agrega los correos electrónicos}
aparece 4 veces en la plantilla (uno por cada nivel), así que un
reemplazo genérico por nombre no alcanza -- se reemplaza usando la
etiqueta que antecede a cada marcador ("✔ Procesado a:", etc.) como
referencia única.
"""

import re
from datetime import datetime

from config.config_reader import Configuracion
from core.motor_plantillas import (
    guardar_plantilla_final,
    leer_plantilla,
    quitar_comentarios,
    reemplazar_marcadores,
)

NOMBRE_ARCHIVO_PLANTILLA = "plantilla_info_inicio_proceso_correo.html"


def _reemplazar_correos_por_etiqueta(html: str, etiqueta: str, correos: list) -> str:
    """
    Reemplaza el primer marcador {...} que aparece después de una
    etiqueta como "✔ Procesado a:", sin afectar los otros marcadores
    idénticos de las demás etiquetas.
    """
    texto_correos = "; ".join(correos) if correos else "(sin destinatarios configurados)"
    patron = re.compile(re.escape(etiqueta) + r"\s*\{[^{}]+\}")
    return patron.sub(f"{etiqueta} {texto_correos}", html, count=1)


def construir_cuerpo_info(config: Configuracion, logger) -> str:
    """
    Arma el cuerpo del correo INFO de inicio de proceso, mostrando qué
    va a hacer el bot y a quién le llegará cada tipo de respuesta,
    según Config.xlsx.
    """
    html = leer_plantilla(NOMBRE_ARCHIVO_PLANTILLA)

    nivel_exitoso = config.correo.obtener_nivel("EXITOSO")
    nivel_advertencia = config.correo.obtener_nivel("ADVERTENCIA")
    nivel_info = config.correo.obtener_nivel("INFO")
    nivel_error = config.correo.obtener_nivel("ERROR")

    html = _reemplazar_correos_por_etiqueta(
        html, "✔ Procesado a:", list(dict.fromkeys(nivel_exitoso.para + nivel_exitoso.copia))
    )
    html = _reemplazar_correos_por_etiqueta(
        html, "⚠ Advertencia a:", list(dict.fromkeys(nivel_advertencia.para + nivel_advertencia.copia))
    )
    html = _reemplazar_correos_por_etiqueta(
        html, "✖ Error a:", list(dict.fromkeys(nivel_error.para + nivel_error.copia))
    )
    html = _reemplazar_correos_por_etiqueta(
        html, "ℹ Información a:", list(dict.fromkeys(nivel_info.para + nivel_info.copia))
    )

    reemplazos = {
        "Descripcion_Proceso": config.proceso.descripcion_proceso,
        "Unidad": config.proceso.unidad,
        # *** ADAPTAR: describe qué va a hacer tu proceso nuevo ***
        "Detalle o resumen de lo que realizará el proceso": (
            "Descripción de lo que hará el proceso -- adaptar a tu robot nuevo."
        ),
        "Lo que se va hacer primero": "Cerrando aplicaciones previas.",
    }

    html_final = reemplazar_marcadores(html, reemplazos)
    html_final = quitar_comentarios(html_final)

    nombre_salida = f"info_{datetime.now().strftime('%d%m%Y_%H%M%S')}.html"
    guardar_plantilla_final(html_final, nombre_salida, logger, prefijo_limpieza="info_")

    return html_final
