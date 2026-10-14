"""
Logger estándar para robots RPA.

Formato obligatorio: dd/MM/yyyy hh:mm:ss tt: [ESTADO] descripción
Estados: INFO, SUCCESS, WARNING, ERROR

Se agrega un nivel personalizado SUCCESS (los niveles estándar de
logging no lo incluyen) para poder registrar hitos positivos del
proceso, como pidieron los estándares técnicos del robot.
"""

import logging
from datetime import datetime
from pathlib import Path

NIVEL_SUCCESS = 25
logging.addLevelName(NIVEL_SUCCESS, "SUCCESS")


class FormateadorProceso(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        marca_tiempo = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p").replace("AM", "am").replace("PM", "pm")
        return f"{marca_tiempo}: [{record.levelname}] {record.getMessage()}"


def crear_logger(nombre_proceso: str, carpeta_log: Path) -> logging.Logger:
    """
    Crea (o reutiliza) el logger del proceso, escribiendo siempre en
    <carpeta_log>/LogTransaccion.log.

    Se usa logger.propagate = False para que los mensajes no dupliquen
    salida en la consola raíz si más de un módulo llama a este logger.
    """
    carpeta_log.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(nombre_proceso)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        manejador_archivo = logging.FileHandler(
            carpeta_log / "LogTransaccion.log", encoding="utf-8"
        )
        manejador_archivo.setFormatter(FormateadorProceso())
        logger.addHandler(manejador_archivo)

        # Salida por consola: el archivo de log sigue siendo la fuente
        # oficial de trazabilidad, pero durante pruebas manuales es
        # indispensable ver el progreso en vivo sin tener que abrir el
        # archivo cada vez.
        manejador_consola = logging.StreamHandler()
        manejador_consola.setFormatter(FormateadorProceso())
        logger.addHandler(manejador_consola)

    # logging no expone un método .success() de forma nativa; se agrega
    # como atajo para respetar el vocabulario de estados pedido (INFO,
    # SUCCESS, WARNING, ERROR) sin que cada módulo repita logger.log(25, ...).
    def success(mensaje: str, *args, **kwargs) -> None:
        logger.log(NIVEL_SUCCESS, mensaje, *args, **kwargs)

    logger.success = success  # type: ignore[attr-defined]
    return logger
