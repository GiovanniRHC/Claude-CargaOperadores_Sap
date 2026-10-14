"""
Utilidad compartida para volcar el árbol de elementos de una ventana
de SAP GUI Scripting -- usada tanto por los scripts de diagnóstico
(diagnostico_zfibp01.py, diagnostico_bp.py) como por el propio código
productivo, cuando un ID esperado falla y conviene auto-diagnosticar
en vez de fallar en silencio.
"""


def volcar_elementos(componente, logger_o_print=print, nivel: int = 0) -> None:
    """
    Recorre recursivamente el árbol de elementos de una ventana SAP e
    imprime/registra el ID técnico, tipo, y texto de cada uno.

    `logger_o_print`: función que recibe un string (ej. print, o
    logger.info) -- así sirve tanto para scripts de diagnóstico
    (print) como para el código productivo (logger.warning/info).
    """
    sangria = "  " * nivel
    try:
        id_tecnico = componente.Id
        tipo = componente.Type
        texto = ""
        try:
            texto = componente.Text
        except Exception:
            pass
        if not texto:
            try:
                texto = componente.Name
            except Exception:
                pass
    except Exception as error:
        logger_o_print(f"{sangria}[no se pudo leer el componente: {error}]")
        return

    logger_o_print(f"{sangria}[{tipo}] {id_tecnico}  ->  '{texto}'")

    try:
        for hijo in componente.Children:
            volcar_elementos(hijo, logger_o_print, nivel + 1)
    except Exception:
        pass
