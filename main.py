"""
Orquestador principal -- PLANTILLA BASE.

*** ADAPTAR AL PROYECTO NUEVO ***
Este archivo tiene la estructura completa y probada (conexión a BD,
correo INFO, manejo de errores garantizado, archivo de estado
garantizado, cierre de aplicaciones garantizado) -- pero el CUERPO del
proceso (la sección marcada "TU LÓGICA DE NEGOCIO AQUÍ") está vacío,
a propósito. Ahí va todo lo específico del proceso nuevo: descargas,
cruces, automatización de la interfaz gráfica, etc.

No cambies el try/finally ni el orden general sin buena razón -- están
así por lecciones aprendidas reales (ver la guía metodológica).
"""

from datetime import datetime
from functools import partial
from pathlib import Path

from config.config_reader import cargar_configuracion, resolver_ruta_config, ConfiguracionInvalidaError, Configuracion
from core.base_datos import conectar, ErrorBaseDatos
from core.captura_pantalla import tomar_captura_pantalla
from core.estado_robot import escribir_estado_robot
from core.logger import crear_logger, FormateadorProceso
from core.manejador_log_bd import ManejadorLogBD
from core.manejo_errores import manejar_error_controlado, manejar_error_inesperado
from core.motor_plantillas import configurar_carpeta_salida
from core.notificaciones import enviar_notificacion, construir_asunto, NivelNotificacion
from proceso.base_datos.registrar_operacion import registrar_operacion, ContextoOperacion
from proceso.base_datos.terminar_proceso_bd import terminar_proceso_bd
from proceso.iniciar_proceso import (
    CarpetasProceso,
    cerrar_aplicaciones_previas,
    crear_estructura_carpetas,
    NOMBRE_PROCESO,
    validar_recurso_existe,
)
from proceso.login.login_sap import iniciar_sesion_sap, ErrorLoginSap
from proceso.reportes.notificar_advertencia import enviar_correo_advertencia
from proceso.reportes.notificar_error_inesperado import enviar_correo_error_inesperado
from proceso.reportes.notificar_resultado import enviar_correo_resultado
from proceso.reportes.notificar_soporte import enviar_correo_soporte
from proceso.reportes.plantilla_info import construir_cuerpo_info


class _EstadoFinalProceso:
    """
    Rastrea cómo terminó el proceso (EXITOSO / ADVERTENCIA / ERROR),
    para escribir estado_robot.txt al final. Empieza en "ERROR" a
    propósito (pesimista): si el proceso muere en cualquier punto sin
    que nadie llegue a actualizar este valor, el archivo de estado debe
    reflejar que algo salió mal, no un valor por defecto engañoso.
    """

    def __init__(self):
        self.valor = "ERROR"


def _crear_notificador_error_controlado(config: Configuracion, tiempo_inicio: datetime, logger):
    return partial(enviar_correo_soporte, config, tiempo_inicio=tiempo_inicio, logger=logger)


def _crear_notificador_error_inesperado(config: Configuracion, tiempo_inicio: datetime, logger):
    return partial(enviar_correo_error_inesperado, config, tiempo_inicio=tiempo_inicio, logger=logger)


def _reportar_error_controlado(mensaje: str, logger, carpetas: CarpetasProceso, notificar_error_controlado) -> None:
    captura = tomar_captura_pantalla(carpetas.screenshot, logger)
    manejar_error_controlado(logger, mensaje, notificar_soporte=notificar_error_controlado, ruta_captura=captura)


def _reportar_error_inesperado(excepcion: Exception, logger, carpetas: CarpetasProceso, notificar_error_inesperado) -> None:
    captura = tomar_captura_pantalla(carpetas.screenshot, logger)
    manejar_error_inesperado(logger, excepcion, notificar_soporte=notificar_error_inesperado, ruta_captura=captura)


def _enviar_correo_info_inicio(config: Configuracion, logger) -> None:
    try:
        nota = config.correo.obtener_nivel(NivelNotificacion.INFO.value).nota
        asunto = construir_asunto(NivelNotificacion.INFO, config.proceso.entorno, config.proceso.nombre_proceso, nota)
        cuerpo_html = construir_cuerpo_info(config, logger)
        enviar_notificacion(NivelNotificacion.INFO, config.correo, asunto=asunto, cuerpo_html=cuerpo_html, logger=logger)
    except Exception as error:
        logger.warning(f"No se pudo enviar el correo INFO de inicio (no detiene el proceso): {error}")


def _ejecutar_flujo_principal(
    config: Configuracion,
    ruta_config: Path,
    tiempo_inicio: datetime,
    carpetas: CarpetasProceso,
    logger,
    notificar_error_controlado,
    conexion_bd,
    contexto_operacion: ContextoOperacion,
    estado_final: _EstadoFinalProceso,
) -> None:
    """
    Cuerpo del proceso. Cada paso debe reportar su propio error
    controlado y retornar (return) para detener el flujo -- el cierre
    de aplicaciones al final NO se hace aquí, se garantiza en
    ejecutar() mediante try/finally, sin importar en qué return se
    haya detenido.
    """
    try:
        validar_recurso_existe(ruta_config, "Config.xlsx")
    except FileNotFoundError as error:
        _reportar_error_controlado(str(error), logger, carpetas, notificar_error_controlado)
        return

    cerrar_aplicaciones_previas(logger)

    try:
        session = iniciar_sesion_sap(config.sap, logger)
    except ErrorLoginSap as error:
        _reportar_error_controlado(str(error), logger, carpetas, notificar_error_controlado)
        return

    logger.info("Login SAP completado.")

    # =========================================================
    # *** TU LÓGICA DE NEGOCIO AQUÍ ***
    #
    # Ejemplo de la forma que suele tomar esto (adaptar):
    #   1. Descargar / obtener los datos de origen.
    #   2. Comparar / validar / cruzar según la regla de negocio.
    #   3. Registrar en base de datos lo que haga falta.
    #   4. Ejecutar la acción real en el sistema con interfaz gráfica
    #      (si corresponde), respetando el patrón de "verificar antes
    #      de actuar" y "validar el resultado exacto, no solo ausencia
    #      de error" -- ver la guía metodológica, secciones 4 y 7.5.
    #   5. Decidir el correo final (EXITOSO / ADVERTENCIA) y actualizar
    #      estado_final.valor en consecuencia.
    #
    # Ejemplo mínimo de correo final exitoso:
    #   enviar_correo_resultado(
    #       config, resumen="Se procesaron N registros correctamente.",
    #       tiempo_inicio=tiempo_inicio, logger=logger,
    #   )
    #   estado_final.valor = "EXITOSO"
    # =========================================================

    logger.info("Proceso finalizado correctamente.")


def ejecutar() -> None:
    tiempo_inicio = datetime.now()

    try:
        ruta_config = resolver_ruta_config()
        config = cargar_configuracion(ruta_config)
    except ConfiguracionInvalidaError as error:
        print(f"[ERROR] No se pudo cargar la configuración: {error}")
        return

    carpetas = crear_estructura_carpetas(config.proceso.carpeta_principal)
    configurar_carpeta_salida(carpetas.correos)
    logger = crear_logger(NOMBRE_PROCESO, carpetas.log)
    logger.info(f"Inicia ejecución del proceso {NOMBRE_PROCESO}")

    notificar_error_controlado = _crear_notificador_error_controlado(config, tiempo_inicio, logger)
    notificar_error_inesperado = _crear_notificador_error_inesperado(config, tiempo_inicio, logger)

    estado_final = _EstadoFinalProceso()

    try:
        conexion_bd = conectar(config.base_datos)
        contexto_operacion = registrar_operacion(conexion_bd, config)
    except ErrorBaseDatos as error:
        _reportar_error_controlado(str(error), logger, carpetas, notificar_error_controlado)
        logger.info("Terminando proceso: cerrando aplicaciones...")
        cerrar_aplicaciones_previas(logger)
        escribir_estado_robot(carpetas.estado_robot, estado_final.valor, logger)
        logger.info("Proceso terminado.")
        return

    manejador_bd = ManejadorLogBD(conexion_bd, contexto_operacion.id_operacion, contexto_operacion.id_registro_principal)
    manejador_bd.setFormatter(FormateadorProceso())
    logger.addHandler(manejador_bd)

    _enviar_correo_info_inicio(config, logger)

    try:
        _ejecutar_flujo_principal(
            config, ruta_config, tiempo_inicio, carpetas, logger, notificar_error_controlado, conexion_bd,
            contexto_operacion, estado_final,
        )
    except Exception as error:
        _reportar_error_inesperado(error, logger, carpetas, notificar_error_inesperado)
    finally:
        logger.info("[INFO] Fin del proceso")
        try:
            terminar_proceso_bd(conexion_bd, config, contexto_operacion)
        except ErrorBaseDatos as error:
            logger.warning(f"No se pudo actualizar el estado final en la base de datos: {error}")
        # SIEMPRE se escribe el archivo de estado -- éxito, advertencia,
        # error controlado, o una excepción totalmente inesperada.
        escribir_estado_robot(carpetas.estado_robot, estado_final.valor, logger)
        logger.info("Terminando proceso: cerrando aplicaciones...")
        cerrar_aplicaciones_previas(logger)
        logger.info("Proceso terminado.")


if __name__ == "__main__":
    ejecutar()
