"""
Conexión a SQL Server y funciones genéricas de bajo nivel para
ejecutar/consultar -- toda la lógica de negocio de qué insertar/
actualizar vive en proceso/base_datos/, no aquí.

Cadena de conexión (especificada por el usuario):
  Driver={ODBC Driver 18 for SQL Server};
  Server=<Servidor>,<Puerto>;
  Database=<BaseDatos>;
  Uid=<Usuario>;
  Pwd=<Password>;
  TrustServerCertificate=Yes;

Requiere el "ODBC Driver 18 for SQL Server" instalado en la máquina
donde corre el robot -- es un driver de Windows aparte, no algo que
pyodbc instale por sí solo. Verificar con el equipo de infraestructura
si la conexión falla con un error de "no se encontró el driver".
"""

import pyodbc

from config.config_reader import ConfiguracionBaseDatos


class ErrorBaseDatos(Exception):
    """Error controlado al conectar o ejecutar contra SQL Server."""


def conectar(config_bd: ConfiguracionBaseDatos):
    """
    Abre una conexión a SQL Server con autocommit activado (cada
    INSERT/UPDATE se confirma de inmediato, sin necesidad de manejar
    transacciones explícitas -- consistente con el patrón "CALL
    ConsultarDataBase" después de cada consulta en Leeme.txt).
    """
    cadena_conexion = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={config_bd.servidor},{config_bd.puerto};"
        f"Database={config_bd.base_datos};"
        f"Uid={config_bd.usuario};"
        f"Pwd={config_bd.password};"
        "TrustServerCertificate=Yes;"
    )
    try:
        conexion = pyodbc.connect(cadena_conexion, timeout=15)
        conexion.autocommit = True
        return conexion
    except pyodbc.Error as error:
        raise ErrorBaseDatos(f"No se pudo conectar a SQL Server: {error}") from error


def ejecutar(conexion, consulta: str, parametros: tuple = ()) -> None:
    """INSERT/UPDATE sin resultado a devolver."""
    try:
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
    except pyodbc.Error as error:
        raise ErrorBaseDatos(f"Error ejecutando consulta SQL: {error}\nConsulta: {consulta}") from error


def consultar_una_fila(conexion, consulta: str, parametros: tuple = ()):
    """SELECT que espera como máximo una fila. Retorna un dict {columna: valor}, o None."""
    try:
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
        fila = cursor.fetchone()
        if fila is None:
            return None
        columnas = [c[0] for c in cursor.description]
        return dict(zip(columnas, fila))
    except pyodbc.Error as error:
        raise ErrorBaseDatos(f"Error consultando SQL: {error}\nConsulta: {consulta}") from error


def consultar_varias_filas(conexion, consulta: str, parametros: tuple = ()) -> list:
    """SELECT que puede devolver varias filas. Retorna una lista de dicts."""
    try:
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
        filas = cursor.fetchall()
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila)) for fila in filas]
    except pyodbc.Error as error:
        raise ErrorBaseDatos(f"Error consultando SQL: {error}\nConsulta: {consulta}") from error
