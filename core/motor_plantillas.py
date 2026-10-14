"""
Motor genérico de plantillas de correo HTML.

Las plantillas ORIGINALES viven en out/*.html (dentro del repositorio
de código) y NUNCA se modifican. Este módulo las lee, reemplaza los
marcadores ({Placeholder} y %Placeholder%) con datos reales, quita los
comentarios de guía (<!-- ... -->, que son solo instrucciones para
quien edita la plantilla, no contenido del correo), y guarda el
resultado final en una carpeta configurable (ver configurar_carpeta_salida).

Dos estilos de marcador conviven en las plantillas:
  - {Placeholder}   -> texto libre a reemplazar (ej. {Descripcion_Proceso})
  - %Placeholder%   -> variables "de sistema" (ej. %ObtenerFechaHoraInicioText%)
Ambos se tratan igual aquí -- un diccionario de reemplazos por nombre.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

RUTA_PLANTILLAS_ORIGEN = Path(__file__).resolve().parent.parent / "out"

# Carpeta donde se guardan los HTML ya generados (con datos reales).
# Por defecto, respaldo dentro del propio repositorio (out/plantillas) --
# pero main.py la reconfigura al inicio para que apunte a la carpeta
# "correos" de C:\RPA\CON02-SSCO_Sunat\ (fuera del repositorio Git), vía
# configurar_carpeta_salida(). Ver proceso/iniciar_proceso.py.
RUTA_PLANTILLAS_SALIDA = RUTA_PLANTILLAS_ORIGEN / "plantillas"

MANTENER_ULTIMAS_PLANTILLAS = 5  # por tipo (info, error, exitoso_con_registro, exitoso_sin_registro)

_PATRON_COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.DOTALL)
_PATRON_MARCADOR = re.compile(r"\{([^{}]+)\}|%(\w+)%")


def configurar_carpeta_salida(ruta: Path) -> None:
    """
    Redirige dónde se guardan los HTML de correo generados -- se llama
    una vez, al inicio de main.py, con la carpeta "correos" (fuera del
    repositorio de código). Si nunca se llama (ej. en los scripts de
    prueba), se sigue usando out/plantillas/ como respaldo.
    """
    global RUTA_PLANTILLAS_SALIDA
    RUTA_PLANTILLAS_SALIDA = Path(ruta)


def formatear_fecha_hora_larga(momento: datetime) -> str:
    """Formato usado dentro del cuerpo del correo: '08/07/2026 01:44:07 a. m.'"""
    fecha = momento.strftime("%d/%m/%Y")
    hora = momento.strftime("%I:%M:%S")
    periodo = "a. m." if momento.hour < 12 else "p. m."
    return f"{fecha} {hora} {periodo}"


def formatear_duracion(duracion: timedelta) -> str:
    """Formato hh:mm:ss, tal como pide la plantilla ('%Duracion% (hh:mm:ss)')."""
    total_segundos = int(duracion.total_seconds())
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def leer_plantilla(nombre_archivo: str) -> str:
    ruta = RUTA_PLANTILLAS_ORIGEN / nombre_archivo
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró la plantilla de correo: {ruta}")
    return ruta.read_text(encoding="utf-8")


def quitar_comentarios(html: str) -> str:
    """Quita los comentarios de guía -- son notas para quien edita la
    plantilla, no deben llegar al correo final."""
    return _PATRON_COMENTARIO_HTML.sub("", html)


def reemplazar_marcadores(html: str, reemplazos: dict) -> str:
    def _sustituir(coincidencia: re.Match) -> str:
        clave = coincidencia.group(1) or coincidencia.group(2)
        if clave in reemplazos:
            return str(reemplazos[clave])
        return coincidencia.group(0)  # marcador no reconocido: se deja tal cual

    return _PATRON_MARCADOR.sub(_sustituir, html)


def _limpiar_plantillas_antiguas(prefijo: str, logger, mantener_ultimas: int = MANTENER_ULTIMAS_PLANTILLAS) -> None:
    """
    Conserva solo las `mantener_ultimas` plantillas más recientes que
    empiecen con `prefijo` (ej. "info_", "error_"), y borra el resto --
    evita que out/plantillas/ crezca sin límite con cada ejecución.
    Se ordena por fecha de modificación real del archivo, no por el
    nombre (el timestamp ddMMyyyy_HHMMSS no ordena cronológicamente
    bien como texto entre meses/años distintos).
    """
    archivos = sorted(
        RUTA_PLANTILLAS_SALIDA.glob(f"{prefijo}*.html"),
        key=lambda ruta: ruta.stat().st_mtime,
        reverse=True,
    )
    for archivo_viejo in archivos[mantener_ultimas:]:
        try:
            archivo_viejo.unlink()
            logger.info(f"Plantilla antigua eliminada (límite de {mantener_ultimas}): {archivo_viejo.name}")
        except OSError as error:
            logger.warning(f"No se pudo eliminar la plantilla antigua {archivo_viejo.name}: {error}")


def guardar_plantilla_final(html_final: str, nombre_salida: str, logger, prefijo_limpieza: str = None) -> Path:
    RUTA_PLANTILLAS_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_salida = RUTA_PLANTILLAS_SALIDA / nombre_salida
    ruta_salida.write_text(html_final, encoding="utf-8")
    logger.info(f"Plantilla de correo generada: {ruta_salida}")

    if prefijo_limpieza:
        _limpiar_plantillas_antiguas(prefijo_limpieza, logger)

    return ruta_salida


def renderizar_plantilla(
    nombre_archivo: str, reemplazos: dict, nombre_salida: str, logger, prefijo_limpieza: str = None
) -> str:
    """
    Caso simple: lee out/<nombre_archivo>, reemplaza los marcadores con
    `reemplazos` (cada nombre de marcador aparece una sola vez en la
    plantilla), quita los comentarios de guía, guarda el resultado en
    out/plantillas/<nombre_salida>, y retorna el HTML final.

    Para plantillas con marcadores repetidos que necesitan valores
    distintos (ej. plantilla INFO), usar leer_plantilla/
    reemplazar_marcadores/guardar_plantilla_final por separado -- ver
    proceso/reportes/plantilla_info.py.
    """
    html_original = leer_plantilla(nombre_archivo)
    html_final = reemplazar_marcadores(html_original, reemplazos)
    html_final = quitar_comentarios(html_final)
    guardar_plantilla_final(html_final, nombre_salida, logger, prefijo_limpieza=prefijo_limpieza)
    return html_final
