"""
Handler de logging que escribe cada línea de log también en la base
de datos: actualiza Operacion.Paso e inserta una fila en LogRobot,
para que el MonitorRPA pueda visualizar el progreso en tiempo real
(confirmado con el usuario: "cada paso que realizas, insértalo en
LogBD").

Se agrega al logger DESPUÉS de RegistrarOperacion, una vez que se
conocen IdOperacion e ID de tu tabla cabecera -- por eso vive separado de
core/logger.py (que se crea antes de conectar a la base de datos).

Un fallo al escribir en la base de datos NUNCA debe tumbar el logging
normal (archivo/consola) ni el proceso -- se atrapa y se ignora
silenciosamente (ya queda registrado en el log de archivo igual).
"""

import logging

from core.base_datos import ejecutar


class ManejadorLogBD(logging.Handler):
    def __init__(self, conexion, id_operacion: int, id_registro_principal: int):
        super().__init__()
        self._conexion = conexion
        self._id_operacion = id_operacion
        self._id_registro_principal = id_registro_principal

    @staticmethod
    def _clasificar_estado(mensaje: str) -> int:
        """1: SUCCESS, 2: WARNING, 3: ERROR, 0: cualquier otro (INFO)."""
        if "SUCCESS" in mensaje:
            return 1
        if "WARNING" in mensaje:
            return 2
        if "ERROR" in mensaje:
            return 3
        return 0

    def emit(self, record: logging.LogRecord) -> None:
        # OJO: no se usa self.format(record) -- ese formato incluye la
        # fecha/hora en el propio texto (para el archivo de log), pero
        # aquí sería redundante: Operacion.FechaActualizacion y
        # LogRobot.FechaRegistro ya guardan la fecha por su cuenta.
        # Se guarda solo "[ESTADO] mensaje", igual al ejemplo de Leeme.txt.
        mensaje = f"[{record.levelname}] {record.getMessage()}"
        try:
            ejecutar(
                self._conexion,
                "UPDATE Operacion SET Paso = ?, FechaActualizacion = GETDATE() WHERE IdOperacion = ?",
                (mensaje, self._id_operacion),
            )
            estado = self._clasificar_estado(mensaje)
            ejecutar(
                self._conexion,
                "INSERT INTO LogRobot (IdentificadorFlujo, Paso, EstadoLogRobot) VALUES (?, ?, ?)",
                (self._id_registro_principal, mensaje, estado),
            )
        except Exception:
            pass
