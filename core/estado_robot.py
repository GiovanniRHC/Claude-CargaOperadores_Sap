"""
Escribe estado_robot.txt en la carpeta EstadoRobot, con el resultado
final de la ejecución (EXITOSO / ADVERTENCIA / ERROR).

Se llama SIEMPRE desde el bloque finally de main.py -- incluso si el
proceso terminó por una excepción no controlada -- para que exista un
archivo de estado predecible en disco después de cada corrida, sin
importar cómo haya terminado.

Nombre fijo (no con fecha/hora): se sobreescribe en cada ejecución, así
cualquier sistema externo que lo lea siempre encuentra el estado de la
corrida MÁS RECIENTE, sin tener que buscar cuál archivo es el último.
"""

from pathlib import Path

NOMBRE_ARCHIVO_ESTADO = "estado_robot.txt"


def escribir_estado_robot(carpeta_estado_robot: Path, estado: str, logger) -> None:
    """
    `estado` debe ser uno de: "EXITOSO", "ADVERTENCIA", "ERROR".

    No lanza excepción si falla -- un problema al escribir este
    archivo no debe impedir que el resto del cierre del proceso
    (cerrar aplicaciones, etc.) se complete igual.
    """
    try:
        ruta_archivo = carpeta_estado_robot / NOMBRE_ARCHIVO_ESTADO
        ruta_archivo.write_text(estado, encoding="utf-8")
        logger.info(f"Estado final del robot registrado en: {ruta_archivo} ({estado})")
    except Exception as error:
        logger.warning(f"No se pudo escribir el archivo de estado del robot: {error}")
