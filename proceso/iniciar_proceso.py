"""
Iniciar Proceso: prepara el entorno de ejecución antes de correr el
cuerpo del robot.

Responsabilidades (una sola por función, según buenas prácticas):
- Crear la estructura de carpetas de trabajo bajo Carpeta_Principal.
- Validar que los recursos necesarios existan.
- Cerrar aplicaciones previas (SAP, navegadores, Excel) para garantizar
  un estado limpio en cada ejecución -- requisito explícito del
  documento de diseño ([el documento de diseño de tu proceso], sección Iniciar Proceso).
"""

import subprocess

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CarpetasProceso:
    raiz: Path
    log: Path
    datos: Path
    screenshot: Path
    reportes: Path
    descargas: Path
    correos: Path
    estado_robot: Path


NOMBRE_PROCESO = "CON04-ArqueoCargaOperadores_Sap"  # debe coincidir con Config.xlsx -> Proceso -> Nombre_Proceso


def crear_estructura_carpetas(carpeta_principal: Path) -> CarpetasProceso:
    """
    Crea (si no existen) las carpetas de trabajo del proceso:
    Log, Datos, Screenshop, Reportes, Descargas, correos -- dentro de
    una carpeta raíz nombrada con el identificador del proceso (la
    misma carpeta donde vive Config.xlsx, ej. C:\\RPA\\CON02-SSCO_Sunat\\).

    "correos" guarda los HTML de correo ya generados (con los datos
    reales reemplazados) en cada ejecución -- vive aquí, fuera del
    repositorio de código, a propósito: si viviera dentro de out/
    (en el repositorio Git), cada ejecución generaría archivos nuevos
    que ensucian el control de versiones, obligando a hacer commit
    constantemente de archivos que no son código. Las plantillas
    ORIGINALES (out/*.html) sí siguen viviendo en el repositorio, solo
    el resultado generado se guarda acá.
    """
    raiz = carpeta_principal / NOMBRE_PROCESO
    carpetas = CarpetasProceso(
        raiz=raiz,
        log=raiz / "Log",
        datos=raiz / "Datos",
        screenshot=raiz / "Screenshop",
        reportes=raiz / "Reportes",
        descargas=raiz / "Descargas",
        correos=raiz / "correos",
        estado_robot=raiz / "EstadoRobot",
    )
    for ruta in (
        carpetas.raiz,
        carpetas.log,
        carpetas.datos,
        carpetas.screenshot,
        carpetas.reportes,
        carpetas.descargas,
        carpetas.correos,
        carpetas.estado_robot,
    ):
        ruta.mkdir(parents=True, exist_ok=True)

    return carpetas


def validar_recurso_existe(ruta_recurso: Path, descripcion: str) -> None:
    """
    Valida que un recurso obligatorio (ej. Config.xlsx) exista antes de
    continuar. Lanza FileNotFoundError con un mensaje claro para que
    ErrorControlado lo capture con contexto útil.
    """
    if not ruta_recurso.exists():
        raise FileNotFoundError(f"Recurso obligatorio no encontrado ({descripcion}): {ruta_recurso}")


PROCESOS_A_CERRAR = ("saplogon.exe", "sapgui.exe", "excel.exe", "chrome.exe")


def _matar_proceso(nombre_proceso: str, logger) -> None:
    """
    Fuerza el cierre de un proceso por nombre (taskkill /F), sin
    esperar a que la aplicación cierre "amablemente". Es intencional:
    no podemos confiar en que una sesión SAP o un Excel huérfano de
    una ejecución anterior estén en un estado sano, así que se
    eliminan por completo en vez de intentar negociar su cierre.
    """
    resultado = subprocess.run(
        ["taskkill", "/IM", nombre_proceso, "/F"],
        capture_output=True,
        text=True,
    )
    salida = (resultado.stdout + resultado.stderr).lower()

    if resultado.returncode == 0:
        logger.info(f"Proceso cerrado: {nombre_proceso}")
    elif "no se encontr" in salida or "not found" in salida:
        logger.info(f"Proceso no estaba en ejecución: {nombre_proceso}")
    else:
        logger.warning(f"No se pudo cerrar el proceso {nombre_proceso}: {salida.strip()}")


def cerrar_aplicaciones_previas(logger) -> None:
    """
    Cierra por la fuerza cualquier instancia de SAP, Excel o Chrome que
    haya quedado abierta de una ejecución anterior, según especifica
    el documento de diseño ([el documento de diseño de tu proceso]). Garantiza un
    estado limpio antes de iniciar el proceso, sin depender de cómo
    haya quedado cada aplicación.
    """
    logger.info("Cerrando aplicaciones previas (SAP, Excel, Chrome)...")
    for proceso in PROCESOS_A_CERRAR:
        _matar_proceso(proceso, logger)
