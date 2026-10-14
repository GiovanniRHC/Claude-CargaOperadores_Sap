"""
Flujo "RegistrarOperacion": se ejecuta UNA sola vez, al iniciar el
proceso. Crea el registro en Operacion (tabla genérica del framework
de RPA de la organización, ya existente -- no la crea este código) y
en la tabla "cabecera" propia de este proceso (configurada como
config.base_datos.tabla_principal en Config.xlsx), y retorna los IDs
que se usarán durante el resto de la ejecución.

*** ADAPTAR AL PROYECTO NUEVO ***
Los nombres de columna "Id" y "IdOperacion" de la tabla cabecera son
un ejemplo -- ajusta ID_COLUMNA_PK_TABLA_PRINCIPAL al nombre real de
la clave primaria de tu propia tabla cabecera (ej. "IdBloqueoSSCO" en
el proyecto SSCO). El resto del patrón (INSERT en Operacion -> obtener
IdOperacion -> INSERT en tu tabla cabecera con ese IdOperacion ->
obtener su propio Id) es genérico y no debería cambiar.
"""

from dataclasses import dataclass

from config.config_reader import Configuracion
from core.base_datos import consultar_una_fila, ejecutar, ErrorBaseDatos

# *** ADAPTAR: nombre real de la clave primaria de tu tabla cabecera ***
ID_COLUMNA_PK_TABLA_PRINCIPAL = "Id"


@dataclass(frozen=True)
class ContextoOperacion:
    id_operacion: int
    id_registro_principal: int


def registrar_operacion(conexion, config: Configuracion) -> ContextoOperacion:
    """
    1. INSERT en Operacion -> obtiene IdOperacion.
    2. INSERT en la tabla cabecera propia (config.base_datos.tabla_principal) -> obtiene su ID.

    Produccion = 1 si Config.xlsx -> Proceso -> Entorno es "PRD", 0 en
    cualquier otro caso.
    """
    produccion = 1 if config.proceso.entorno.strip().upper() == "PRD" else 0

    ejecutar(
        conexion,
        "INSERT INTO Operacion (IdentificadorBot, NombreProceso, Produccion) VALUES (?, ?, ?)",
        (config.proceso.identificador_bot, config.proceso.nombre_proceso, produccion),
    )
    fila_operacion = consultar_una_fila(
        conexion,
        "SELECT TOP 1 * FROM Operacion WHERE NombreProceso = ? ORDER BY IdOperacion DESC",
        (config.proceso.nombre_proceso,),
    )
    if fila_operacion is None:
        raise ErrorBaseDatos("No se pudo leer el IdOperacion recién insertado en Operacion.")
    id_operacion = fila_operacion["IdOperacion"]

    ejecutar(
        conexion,
        f"INSERT INTO {config.base_datos.tabla_principal} (IdOperacion) VALUES (?)",
        (id_operacion,),
    )
    fila_registro_principal = consultar_una_fila(
        conexion,
        f"SELECT TOP 1 * FROM {config.base_datos.tabla_principal} ORDER BY {ID_COLUMNA_PK_TABLA_PRINCIPAL} DESC",
    )
    if fila_registro_principal is None:
        raise ErrorBaseDatos(
            f"No se pudo leer el ID recién insertado en {config.base_datos.tabla_principal}."
        )
    id_registro_principal = fila_registro_principal[ID_COLUMNA_PK_TABLA_PRINCIPAL]

    return ContextoOperacion(id_operacion=id_operacion, id_registro_principal=id_registro_principal)
