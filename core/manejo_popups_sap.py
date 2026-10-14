"""
Manejo de los popups "Seguridad SAP GUI" que aparecen al descargar
archivos vía scripting -- protección nativa de SAP GUI contra scripts
que acceden al sistema de archivos local (el mecanismo detrás de
GUI_DOWNLOAD y funciones similares).

Este popup puede aparecer más de una vez en secuencia (una por carpeta
o subcarpeta a autorizar), así que se revisa en bucle hasta que ya no
aparezca más, con un límite de intentos por seguridad.

IDs de los controles: NO están confirmados contra el entorno real (a
diferencia de ZFIBP01, que sí se validó con diagnostico_zfibp01.py).
Se usa el patrón estándar de los popups simples de SAP (grupo de
función SPOP). Si el ID falla, en vez de fallar en silencio, se vuelca
el árbol completo de la ventana al log -- así se puede corregir en un
solo intento más si el supuesto está equivocado, en vez de adivinar a
ciegas otra vez.
"""

MAXIMO_POPUPS_SEGURIDAD = 5
TEXTO_TITULO_SEGURIDAD = "seguridad"


class ErrorPopupSeguridadDesconocido(Exception):
    """
    Se lanza cuando aparece el popup de seguridad pero su estructura no
    coincide con los IDs supuestos -- el árbol de la ventana ya quedó
    volcado en el log para poder corregir los IDs.
    """


def _volcar_elementos(componente, logger, nivel: int = 0) -> None:
    sangria = "  " * nivel
    try:
        id_tecnico = componente.Id
        tipo = componente.Type
        texto = getattr(componente, "Text", "") or ""
    except Exception:
        return
    logger.info(f"{sangria}[{tipo}] {id_tecnico}  ->  '{texto}'")
    try:
        for hijo in componente.Children:
            _volcar_elementos(hijo, logger, nivel + 1)
    except Exception:
        pass


def _buscar_ventana_seguridad(session):
    """
    Busca, entre las ventanas emergentes (wnd[1], wnd[2], ...), una
    cuyo título contenga "seguridad". Retorna None si no hay ninguna.
    """
    for indice in range(1, 4):  # wnd[1] a wnd[3]: rango razonable, no
                                 # debería haber más ventanas apiladas.
        try:
            ventana = session.FindById(f"wnd[{indice}]")
        except Exception:
            return None
        try:
            titulo = ventana.Text
        except Exception:
            titulo = ""
        if TEXTO_TITULO_SEGURIDAD in titulo.lower():
            return ventana
    return None


def manejar_popups_seguridad_sap(session, logger) -> None:
    """
    Revisa y cierra, en bucle, los popups de "Seguridad SAP GUI" que
    puedan aparecer tras ejecutar una descarga. Marca "Recordar mi
    decisión" antes de aceptar, para reducir que vuelvan a aparecer en
    corridas futuras para la misma carpeta.

    No hace nada si no aparece ningún popup -- es seguro llamarla
    siempre después de una operación que dispare una descarga.
    """
    for _ in range(MAXIMO_POPUPS_SEGURIDAD):
        ventana = _buscar_ventana_seguridad(session)
        if ventana is None:
            return

        logger.warning("Popup de 'Seguridad SAP GUI' detectado. Autorizando...")

        try:
            ventana.FindById("usr/chkPermanent").select()
        except Exception:
            logger.warning(
                "No se pudo marcar 'Recordar mi decisión' (ID supuesto incorrecto). "
                "Se continúa igual, solo no se recordará la decisión."
            )

        try:
            ventana.FindById("usr/btnSPOP-OPTION1").press()
            logger.info("Popup de seguridad autorizado ('Permitir').")
        except Exception as error:
            logger.error(
                f"No se pudo presionar 'Permitir' con el ID esperado ({error}). "
                "Volcando estructura real de la ventana para corregir los IDs:"
            )
            _volcar_elementos(ventana, logger)
            raise ErrorPopupSeguridadDesconocido(
                "El popup de seguridad SAP GUI tiene una estructura distinta a la "
                "esperada. Revisar el log para los IDs reales y ajustar este módulo."
            )
