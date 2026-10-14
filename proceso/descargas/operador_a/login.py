"""
Login al portal OperadorA (comerciosoperador_aclub.pe) -- PENDIENTE.

Este módulo todavía no tiene código real a propósito: según la guía
metodológica (sección 3), los selectores de una interfaz gráfica nunca
se adivinan. Antes de escribir esta función hace falta:

  1. Correr diagnosticos/diagnostico_login_operador_a.py y confirmar los
     selectores reales del formulario de login (usuario, contraseña,
     botón) y cómo está armado el reCAPTCHA (iframe simple tipo
     checkbox, o un challenge de imágenes -- esto último cambiaría el
     enfoque por completo, ver nota abajo).
  2. Con esos selectores confirmados, escribir aquí el login real con
     Playwright, siguiendo el mismo patrón que proceso/login/login_sap.py
     (una función iniciar_sesion_operador_a(config_sociedad, logger) que
     retorne la `page` ya logueada, y una excepción propia
     ErrorLoginOperadorA para errores controlados).

Nota sobre el reCAPTCHA: si resulta ser un checkbox simple ("No soy un
robot") sin challenge visual detrás, Playwright suele poder resolverlo
solo en la mayoría de los casos (Google evalúa señales de
comportamiento, no solo el click). Si dispara un challenge de
imágenes, NO hay forma confiable de resolverlo de forma 100%
automática sin un servicio externo de resolución de captcha -- eso
implicaría una decisión de negocio (¿aprobar un servicio de terceros
pago?) antes de seguir, no algo que se pueda programar por las buenas.
"""

# *** PENDIENTE: implementar iniciar_sesion_operador_a() con los selectores
# confirmados por diagnosticos/diagnostico_login_operador_a.py ***
