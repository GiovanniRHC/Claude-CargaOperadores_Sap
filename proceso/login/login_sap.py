"""
Login a SAP vía SAP GUI Scripting.

Requiere (validar en el entorno de ejecución antes de la primera corrida real):
  1. SAP GUI Scripting habilitado en el cliente (SAP Logon > Opciones >
     Accesibilidad y Scripts > Habilitar Scripting). -- CONFIRMADO por el
     usuario, ya está habilitado.
  2. Parámetro de servidor sapgui/user_scripting = TRUE (a confirmar con
     el equipo Basis).
  3. Que config_sap.nombre_conexion coincida EXACTAMENTE con el nombre
     de la conexión configurada en el SAP Logon Pad de la máquina donde
     corre el robot. -- CONFIRMADO, coincide carácter por carácter.

Sobre el manejo de sesión múltiple: según el campo "Nota" de Config.xlsx,
si SAP muestra la advertencia de que el usuario ya tiene otra sesión
abierta, el bot debe continuar sin finalizar esa otra sesión. Esa lógica
se aplica en _manejar_ventana_sesion_multiple.

IMPORTANTE: los IDs de los campos de la ventana de sesión múltiple
(wnd[1]/...) corresponden al comportamiento estándar de SAP GUI, pero
DEBEN validarse en el ambiente real con el grabador de Scripting Tracker
antes de dar este módulo por cerrado -- distintas versiones de SAP GUI
pueden nombrar estos controles de forma distinta. Esto queda pendiente
para la fase de pruebas unitarias, tal como acordamos.

SOBRE EL AUTO-ARRANQUE DE SAP LOGON:
Iniciar Proceso cierra SAP Logon (taskkill /F) para garantizar estado
limpio en cada ejecución. Esto significa que, al llegar aquí, SAP Logon
casi seguro NO está corriendo -- por eso este módulo lo abre de nuevo
él mismo si GetObject("SAPGUI") falla, en vez de asumir que alguien lo
dejó abierto manualmente.
"""

import subprocess
import time
from pathlib import Path

import win32com.client

from config.config_reader import ConfiguracionSap
from core.volcar_elementos_sap import volcar_elementos

SEGUNDOS_ESPERA_INICIO_SAPLOGON = 20

# Rutas de instalación típicas de SAP GUI para Windows. Se usan como
# respaldo si Config.xlsx no trae la columna opcional RutaSapLogon, o
# si esa ruta configurada no existe en la máquina.
RUTAS_SAPLOGON_CONOCIDAS = (
    r"C:\Program Files (x86)\SAP\FrontEnd\SapGui\saplogon.exe",
    r"C:\Program Files\SAP\FrontEnd\SapGui\saplogon.exe",
)


class ErrorLoginSap(Exception):
    """Error controlado durante el inicio de sesión en SAP."""


def _resolver_ruta_saplogon(config_sap: ConfiguracionSap) -> Path:
    """
    Determina qué ejecutable de SAP Logon usar: primero la ruta
    explícita en Config.xlsx (si existe y el archivo está presente),
    luego las rutas conocidas de instalación estándar.
    """
    candidatas = []
    if config_sap.ruta_sap_logon:
        candidatas.append(config_sap.ruta_sap_logon)
    candidatas.extend(RUTAS_SAPLOGON_CONOCIDAS)

    for candidata in candidatas:
        ruta = Path(candidata)
        if ruta.exists():
            return ruta

    raise ErrorLoginSap(
        "SAP Logon no está en ejecución y no se encontró su ejecutable en "
        f"ninguna ruta conocida ({', '.join(candidatas)}). Agregar la ruta "
        "correcta en Config.xlsx, hoja Sap, columna RutaSapLogon."
    )


def _iniciar_saplogon_y_esperar(config_sap: ConfiguracionSap, logger):
    """
    Abre SAP Logon y espera hasta que el motor de scripting quede
    disponible (GetObject("SAPGUI") deja de fallar), con un límite de
    tiempo -- para no quedar esperando para siempre si algo más
    impide que SAP Logon termine de iniciar.
    """
    ruta_saplogon = _resolver_ruta_saplogon(config_sap)
    logger.info(f"SAP Logon no estaba en ejecución. Iniciando desde: {ruta_saplogon}")
    subprocess.Popen([str(ruta_saplogon)])

    limite = time.time() + SEGUNDOS_ESPERA_INICIO_SAPLOGON
    while time.time() < limite:
        try:
            return win32com.client.GetObject("SAPGUI")
        except Exception:
            time.sleep(1)

    raise ErrorLoginSap(
        f"SAP Logon no terminó de iniciar tras {SEGUNDOS_ESPERA_INICIO_SAPLOGON} "
        "segundos. Verificar manualmente si abre correctamente."
    )


def _obtener_motor_scripting(config_sap: ConfiguracionSap, logger):
    logger.info("Conectando con SAP GUI Scripting (GetObject 'SAPGUI')...")
    try:
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
    except Exception:
        sap_gui_auto = _iniciar_saplogon_y_esperar(config_sap, logger)

    logger.info("Conexión con SAP GUI Scripting establecida.")
    return sap_gui_auto.GetScriptingEngine


def _abrir_conexion(motor_scripting, nombre_conexion: str, logger):
    """
    Abre una conexión SAP nueva.

    No se busca ni se reutiliza ninguna conexión existente: el módulo
    de Iniciar Proceso (cerrar_sesiones_sap_existentes) garantiza que
    no queda ninguna conexión abierta antes de llegar aquí, tal como
    especifica el documento de diseño ("cerrar y volver a abrir").
    Esto elimina la ambigüedad de no saber en qué estado quedó una
    sesión previa.
    """
    logger.info(f"Abriendo conexión SAP: {nombre_conexion}")
    logger.info("Esto puede tardar 10-30 segundos la primera vez.")
    try:
        conexion = motor_scripting.OpenConnection(nombre_conexion, True)
    except Exception as error:
        raise ErrorLoginSap(
            f"No se pudo abrir la conexión '{nombre_conexion}'. Verificar que "
            "el nombre coincida exactamente con el configurado en SAP Logon Pad."
        ) from error
    logger.info("Conexión SAP abierta correctamente.")
    return conexion


def _completar_pantalla_login(session, config_sap: ConfiguracionSap) -> None:
    session.FindById("wnd[0]/usr/txtRSYST-MANDT").text = config_sap.mandante
    session.FindById("wnd[0]/usr/txtRSYST-BNAME").text = config_sap.usuario
    session.FindById("wnd[0]/usr/pwdRSYST-BCODE").text = config_sap.password
    session.FindById("wnd[0]/usr/txtRSYST-LANGU").text = config_sap.idioma
    session.FindById("wnd[0]").sendVKey(0)  # Enter


def _manejar_ventana_sesion_multiple(session, logger) -> None:
    """
    Si aparece la ventana de advertencia de sesión múltiple, selecciona
    la opción "continuar sin finalizar otras sesiones", según lo
    indicado en el campo Nota de Config.xlsx.

    ID del radio button CONFIRMADO por el usuario (capturado con Power
    Automate Desktop, conector SAP -- es el mismo árbol de SAP GUI
    Scripting que usamos aquí, no una API distinta):
        /app/con[0]/ses[0]/wnd[1]/usr/radMULTI_LOGON_OPT2

    PENDIENTE: el ID del botón "Confirmar selección" (hoy
    "tbar[0]/btn[0]") sigue siendo un supuesto, no confirmado -- si
    falla, hay que capturarlo con el mismo método.

    Si la ventana no aparece, se continúa el flujo normalmente.
    """
    try:
        ventana_alerta = session.FindById("wnd[1]")
    except Exception:
        return

    logger.warning(
        "Se detectó una sesión SAP previa con el mismo usuario. "
        "Se continúa sin cerrar la otra sesión, según Config.xlsx."
    )
    ventana_alerta.FindById("usr/radMULTI_LOGON_OPT2").select()
    try:
        ventana_alerta.FindById("tbar[0]/btn[0]").press()
    except Exception as error:
        logger.error(
            f"No se pudo presionar el botón de confirmar con el ID esperado ({error}). "
            "Volcando estructura real de la ventana para corregir el ID:"
        )
        volcar_elementos(ventana_alerta, logger.info)
        raise ErrorLoginSap(
            "El botón de confirmar de la ventana de sesión múltiple tiene un ID "
            "distinto al esperado. Revisar el log para los IDs reales."
        ) from error


def _validar_login_exitoso(session) -> None:
    barra_estado = session.FindById("wnd[0]/sbar")
    if barra_estado.MessageType == "E":
        raise ErrorLoginSap(f"SAP rechazó el inicio de sesión: {barra_estado.Text}")


def iniciar_sesion_sap(config_sap: ConfiguracionSap, logger):
    """
    Punto único de entrada para iniciar sesión en SAP.

    Retorna el objeto `session` de SAP GUI Scripting, listo para que
    los módulos siguientes (Descargas, SAP/Bloqueo) naveguen transacciones.
    """
    motor_scripting = _obtener_motor_scripting(config_sap, logger)
    conexion = _abrir_conexion(motor_scripting, config_sap.nombre_conexion, logger)
    session = conexion.Children(0)

    _completar_pantalla_login(session, config_sap)
    _manejar_ventana_sesion_multiple(session, logger)
    _validar_login_exitoso(session)

    logger.success(
        f"Sesión SAP iniciada correctamente. Usuario: {config_sap.usuario}, "
        f"Mandante: {config_sap.mandante}"
    )
    return session
