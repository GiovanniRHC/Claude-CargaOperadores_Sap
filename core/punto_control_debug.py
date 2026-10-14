"""
Utilidad de SOLO DEBUG -- muestra un popup con dos botones
(Continuar/Detener) después de cada paso importante, para verificar
manualmente que el bot esté siguiendo el flujo correcto en SAP.

*** NUNCA debe quedar activo en una corrida productiva desatendida ***
El bot se queda esperando un clic humano en cada punto de control --
esto rompe por completo la automatización sin supervisión.

Se activa llamando activar_puntos_control() explícitamente (por
ejemplo, al inicio de un script de prueba) -- por defecto está
apagado, y punto_control() no hace nada (retorna de inmediato) si no
se activó. IMPORTANTE: tkinter se importa recién dentro de
punto_control(), no al cargar este módulo -- así, si tkinter no está
disponible en el Python de la máquina (poco común, pero posible en
instalaciones mínimas), el bot en modo normal (sin debug) nunca se ve
afectado.
"""

_ACTIVO = False


class ErrorDetenidoPorUsuario(Exception):
    """El usuario eligió 'Detener' en un punto de control de debug."""


def activar_puntos_control() -> None:
    global _ACTIVO
    _ACTIVO = True


def desactivar_puntos_control() -> None:
    global _ACTIVO
    _ACTIVO = False


def puntos_control_activos() -> bool:
    return _ACTIVO


def punto_control(mensaje: str) -> None:
    """
    Si los puntos de control están activos, muestra un popup con
    Continuar/Detener y espera la decisión del usuario -- bloquea la
    ejecución hasta que se haga clic en alguno de los dos.

    Si no están activos (comportamiento normal en producción), no hace
    nada y retorna de inmediato -- costo prácticamente nulo.

    Si el usuario elige "Detener", lanza ErrorDetenidoPorUsuario.
    """
    if not _ACTIVO:
        return

    try:
        import tkinter as tk
    except ImportError as error:
        raise RuntimeError(
            "Los puntos de control de debug requieren tkinter, que no está disponible "
            f"en este Python ({error}). Instálalo o desactiva --paso-a-paso."
        ) from error

    resultado = {"continuar": True}

    def _continuar():
        resultado["continuar"] = True
        ventana.destroy()

    def _detener():
        resultado["continuar"] = False
        ventana.destroy()

    ventana = tk.Tk()
    ventana.title("Punto de control (DEBUG)")
    ventana.attributes("-topmost", True)
    tk.Label(ventana, text=mensaje, padx=20, pady=20, wraplength=420, justify="left").pack()
    marco_botones = tk.Frame(ventana, pady=10)
    marco_botones.pack()
    tk.Button(marco_botones, text="Continuar", width=12, command=_continuar).pack(side="left", padx=10)
    tk.Button(marco_botones, text="Detener", width=12, command=_detener).pack(side="left", padx=10)

    # Centrar la ventana en pantalla.
    ventana.update_idletasks()
    ancho, alto = ventana.winfo_width(), ventana.winfo_height()
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f"+{x}+{y}")

    ventana.mainloop()

    if not resultado["continuar"]:
        raise ErrorDetenidoPorUsuario(f"El usuario detuvo el proceso en: {mensaje}")
