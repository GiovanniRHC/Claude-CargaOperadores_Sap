"""
Script de DIAGNÓSTICO -- PLANTILLA BASE, no forma parte del robot productivo.

*** ADAPTAR AL PROYECTO NUEVO ***
Este es el patrón que más tiempo ahorró en el proyecto anterior: en
vez de adivinar selectores técnicos de una pantalla nueva, se navega
hasta ahí reutilizando el login ya probado, y se vuelca toda la
estructura técnica de la pantalla -- así se consiguen los IDs reales
para construir la función definitiva, sin adivinar.

Uso:
    py diagnostico_ejemplo.py <parámetro de prueba, ej. un código>

Flujo típico de uso:
  1. Correr este script -- va a fallar en el primer punto que no
     tenga un selector confirmado (es esperado la primera vez).
  2. El volcado de pantalla que imprime muestra la estructura real --
     buscar ahí el campo/botón que se necesita.
  3. Agregar ese selector real al código productivo.
  4. Repetir para la siguiente pantalla del flujo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.config_reader import cargar_configuracion, resolver_ruta_config
from core.logger import crear_logger
from core.volcar_elementos_sap import volcar_elementos
from proceso.iniciar_proceso import (
    cerrar_aplicaciones_previas,
    crear_estructura_carpetas,
    NOMBRE_PROCESO,
)
from proceso.login.login_sap import iniciar_sesion_sap


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: py diagnostico_ejemplo.py <parámetro de prueba>")
        return

    parametro_prueba = sys.argv[1]

    config = cargar_configuracion(resolver_ruta_config())
    carpetas = crear_estructura_carpetas(config.proceso.carpeta_principal)
    logger = crear_logger(NOMBRE_PROCESO, carpetas.log)

    cerrar_aplicaciones_previas(logger)
    session = iniciar_sesion_sap(config.sap, logger)

    print("\n*** ADAPTAR: navega aquí a la transacción/pantalla que necesitas investigar ***")
    # Ejemplo (transacción de SAP):
    # session.FindById("wnd[0]/tbar[0]/okcd").text = "/nTU_TRANSACCION"
    # session.FindById("wnd[0]").sendVKey(0)

    print("--- Elementos de la pantalla wnd[0] ---\n")
    volcar_elementos(session.FindById("wnd[0]"), print)

    print("\n--- Fin del volcado ---")
    print("\nBusca en esta lista el campo/botón que necesitas -- copia su ID técnico")
    print("completo (la ruta wnd[...]/... completa) tal cual aparece en el volcado.")


if __name__ == "__main__":
    main()
