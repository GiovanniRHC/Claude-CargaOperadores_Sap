"""
Punto único de envío de correos del bot, y formato estándar de asunto
según el nivel de notificación.

Los DESTINATARIOS y el texto del asunto (Nota) se leen directamente de
Config.xlsx, hoja Correo (una fila por nivel) -- ver
config/config_reader.py, ConfiguracionCorreo.obtener_nivel(). Este
módulo no calcula ni hardcodea ninguna regla de negocio sobre a quién
le llega cada correo.

Este proceso usa 6 niveles (no los 5 de la plantilla base): EXITOSO
viene desdoblado en EXITOSO_CON_REGISTRO / EXITOSO_SIN_REGISTRO --
mismo patrón que ya usó el proyecto SSCO cuando el correo de éxito se
veía distinto según si había datos que mostrar. Cada nivel tiene su
propia fila en la hoja Correo de Config.xlsx (ya confirmado: los 6
nombres de esta enum coinciden exactamente con los 6 valores de la
columna "Nivel" del Config.xlsx real de este proceso).

Formato de asunto:
  [ICONO] ETIQUETA {Entorno}-{NombreProceso} {Nota del nivel} - {fecha hora}

  Ejemplos:
    [✔] PROCESADO QAS-CON04-ArqueoCargaOperadores_Sap Proceso ejecutado correctamente - 07/07/2026 01:44 a. m.
    [✖] ERROR QAS-CON04-ArqueoCargaOperadores_Sap Proceso incompleto - 07/07/2026 01:44 a. m.
    [ℹ] INFO QAS-CON04-ArqueoCargaOperadores_Sap Proceso estado actual - 07/07/2026 01:44 a. m.
    [⚠] ADVERTENCIA QAS-CON04-ArqueoCargaOperadores_Sap Proceso ejecutado con observaciones - 07/07/2026 01:44 a. m.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from config.config_reader import ConfiguracionCorreo
from core.enviar_correo_smtp import enviar_correo_smtp, ErrorEnvioCorreo


class NivelNotificacion(str, Enum):
    INFO = "INFO"
    EXITOSO_CON_REGISTRO = "EXITOSO_CON_REGISTRO"
    EXITOSO_SIN_REGISTRO = "EXITOSO_SIN_REGISTRO"
    ADVERTENCIA = "ADVERTENCIA"
    ERROR = "ERROR"
    ERROR_INESPERADO = "ERROR_INESPERADO"


_ICONOS = {
    NivelNotificacion.INFO: "ℹ",
    NivelNotificacion.EXITOSO_CON_REGISTRO: "✔",
    NivelNotificacion.EXITOSO_SIN_REGISTRO: "✔",
    NivelNotificacion.ADVERTENCIA: "⚠",
    NivelNotificacion.ERROR: "✖",
    NivelNotificacion.ERROR_INESPERADO: "✖",
}

_ETIQUETAS = {
    NivelNotificacion.INFO: "INFO",
    NivelNotificacion.EXITOSO_CON_REGISTRO: "PROCESADO",
    NivelNotificacion.EXITOSO_SIN_REGISTRO: "PROCESADO",
    NivelNotificacion.ADVERTENCIA: "ADVERTENCIA",
    NivelNotificacion.ERROR: "ERROR",
    NivelNotificacion.ERROR_INESPERADO: "ERROR",
}


def _formatear_fecha_hora(momento: datetime) -> str:
    """
    Formatea como '07/07/2026 01:44 a. m.' -- no se usa el locale del
    sistema (strftime %p depende de la configuración regional de cada
    máquina), se construye a mano para que el formato sea idéntico sin
    importar en qué servidor corra el bot.
    """
    fecha = momento.strftime("%d/%m/%Y")
    hora = momento.strftime("%I:%M")
    periodo = "a. m." if momento.hour < 12 else "p. m."
    return f"{fecha} {hora} {periodo}"


def construir_asunto(
    nivel: NivelNotificacion,
    entorno: str,
    nombre_proceso: str,
    mensaje: str,
    momento: Optional[datetime] = None,
) -> str:
    """
    Construye el asunto estándar del correo:
    [ICONO] ETIQUETA Entorno-NombreProceso mensaje - fecha hora

    `mensaje` viene de Config.xlsx (columna Nota de la hoja Correo,
    ver ConfiguracionCorreoNivel.nota) -- nunca hardcodeado en Python.
    """
    momento = momento or datetime.now()
    icono = _ICONOS[nivel]
    etiqueta = _ETIQUETAS[nivel]
    fecha_hora = _formatear_fecha_hora(momento)
    return f"[{icono}] {etiqueta} {entorno}-{nombre_proceso} {mensaje} - {fecha_hora}"


def enviar_notificacion(
    nivel: NivelNotificacion,
    config_correo: ConfiguracionCorreo,
    asunto: str,
    cuerpo_html: str,
    logger,
    ruta_adjunto: Optional[Path] = None,
    adjuntos_adicionales: Optional[list] = None,
) -> None:
    """
    Punto único de envío de cualquier correo del bot. Busca
    destinatarios/copia para el nivel dado en config_correo (leído de
    Config.xlsx), y delega el envío real a enviar_correo_smtp.

    No lanza excepción si el envío falla -- solo lo registra como
    advertencia, para que un problema de correo nunca oculte ni
    reemplace lo que realmente pasó en el proceso.
    """
    nivel_config = config_correo.obtener_nivel(nivel.value)
    try:
        enviar_correo_smtp(
            config_correo,
            destinatarios=nivel_config.para,
            copia=nivel_config.copia,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            logger=logger,
            ruta_adjunto=ruta_adjunto,
            adjuntos_adicionales=adjuntos_adicionales,
        )
    except ErrorEnvioCorreo as error:
        logger.warning(str(error))
