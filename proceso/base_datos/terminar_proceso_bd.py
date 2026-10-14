"""
Flujo "TerminarProceso", lado base de datos: actualiza el estado final
en Operacion y en la tabla cabecera propia del proceso. El log
"[INFO] Fin del proceso" que dispara esto se escribe por separado, vía
el logger normal (que ya cascada a Operacion.Paso + LogRobot a través
de ManejadorLogBD).

*** ADAPTAR AL PROYECTO NUEVO ***
Los nombres de columna de la tabla cabecera (ID_COLUMNA_PK, columna de
estado, columna de fecha) son un ejemplo -- ajústalos a los nombres
reales de tu tabla (ej. "IdBloqueoSSCO"/"EstadoBloqueoSSCO" en el
proyecto SSCO).
"""

from config.config_reader import Configuracion
from core.base_datos import ejecutar
from proceso.base_datos.registrar_operacion import ContextoOperacion, ID_COLUMNA_PK_TABLA_PRINCIPAL

# *** ADAPTAR: nombres reales de las columnas de estado/fecha de tu tabla cabecera ***
COLUMNA_ESTADO_TABLA_PRINCIPAL = "Estado"
COLUMNA_FECHA_ACTUALIZACION_TABLA_PRINCIPAL = "FechaActualizacion"


def terminar_proceso_bd(conexion, config: Configuracion, contexto: ContextoOperacion) -> None:
    ejecutar(
        conexion,
        "UPDATE Operacion SET Observacion = '', EstadoOperacion = 1 WHERE IdOperacion = ?",
        (contexto.id_operacion,),
    )
    ejecutar(
        conexion,
        f"UPDATE {config.base_datos.tabla_principal} "
        f"SET {COLUMNA_ESTADO_TABLA_PRINCIPAL} = 1, {COLUMNA_FECHA_ACTUALIZACION_TABLA_PRINCIPAL} = GETDATE() "
        f"WHERE {ID_COLUMNA_PK_TABLA_PRINCIPAL} = ?",
        (contexto.id_registro_principal,),
    )
