# CON04-ArqueoCargaOperadores_Sap

Robot RPA: descarga de reportes de operadores (OperadorB,
OperadorC, OperadorA), cruce con SAP, carga a SAP vía transacción Z
(Arqueo de Operadores). Construido a partir de la plantilla base del
proyecto CON02-SSCO_Sunat, siguiendo `Metodologia_Automatizacion_RPA_con_Claude.md`
(guardada también en el proyecto de Claude, junto con la bitácora de
avance -- ambas sirven de contexto si se retoma este trabajo en otra
sesión).

**Estado actual: esqueleto de configuración/orquestación adaptado.
Ningún módulo de negocio (portales, cruce, carga SAP) está construido
todavía** -- se está esperando confirmar selectores reales y cerrar
varios pendientes de datos antes de escribir esa parte (ver abajo).

## Qué es 100% reutilizable tal cual (heredado de la plantilla base)

- `core/logger.py`, `core/manejo_errores.py`, `core/captura_pantalla.py`
- `core/enviar_correo_smtp.py`, `core/motor_plantillas.py`
- `core/base_datos.py`, `core/manejador_log_bd.py`
- `core/volcar_elementos_sap.py`, `core/punto_control_debug.py`
- `core/estado_robot.py`, `core/manejo_popups_sap.py`
- `proceso/login/login_sap.py` (login completo a SAP)

## Qué ya se adaptó a este proceso específico

- `config/config_reader.py` -- agrega lectura de las hojas propias
  `Operadores` y `Sociedades` del `Config.xlsx` real (la plantilla base
  no las tenía). Falla explícitamente si algún portal activo
  (`Ingresar=SI`) no tiene sociedades cargadas, en vez de dejarlo
  pasar en silencio.
- `core/notificaciones.py` -- 6 niveles (no 5): `EXITOSO` viene
  desdoblado en `EXITOSO_CON_REGISTRO`/`EXITOSO_SIN_REGISTRO`, tal
  como ya trae el `Config.xlsx` real.
- `proceso/reportes/notificar_resultado.py` -- ahora recibe
  `con_registros: bool` para elegir el nivel de éxito correcto.
- `proceso/iniciar_proceso.py` -- `NOMBRE_PROCESO = "CON04-ArqueoCargaOperadores_Sap"`.
- `requirements.txt` -- se agregó `playwright` (la plantilla base solo
  traía lo necesario para SAP GUI Scripting, no para portales web).
- `config/RutaArchivoConfig.txt` -- apunta (como placeholder, a
  confirmar) a `C:\RPA\CON04-ArqueoCargaOperadores_Sap\Config.xlsx`.

## Qué sigue pendiente antes de poder construir la lógica de negocio

Ver la bitácora del proyecto para el detalle completo. Resumen de lo
que bloquea avanzar:

- URLs de login reales de OperadorB y OperadorC (`Config.xlsx` trae "Por
  definir") -- pendiente de que el negocio las defina.
- Sociedades de OperadorC: la hoja `Sociedades` no tiene ninguna fila
  para ese portal.
- `DataBase.TablaPrincipal` vacío -- falta diseñar y nombrar la tabla
  cabecera propia de este proceso en SQL Server.
- Selectores reales del portal OperadorA -- primer diagnóstico en curso
  (ver `diagnosticos/diagnostico_login_operador_a.py`).
- Reglas de negocio del ENT todavía sin cerrar (formato del reporte
  consolidado único, manejo del filtro "Red" en OperadorA, rango de
  fechas de descarga por corrida, etc.)

## Diagnósticos (selectores reales, sin adivinar)

- `diagnosticos/diagnostico_login_operador_a.py` -- primer script, solo
  lectura, sin credenciales: vuelca la estructura del formulario de
  login de OperadorA. Correrlo y pegar `resultado.json` de vuelta antes
  de escribir `proceso/descargas/operador_a/login.py`.
- `diagnostico_ejemplo.py` (raíz) -- plantilla original para pantallas
  de SAP (reutiliza el login SAP ya confirmado). Copiar una vez por
  cada transacción nueva que haya que investigar.

## Estructura de `proceso/descargas/`

Un módulo por portal, mismo patrón que el resto del robot (una
responsabilidad por archivo). Hoy solo existe la carpeta de OperadorA
(con un `login.py` placeholder, sin selectores todavía) -- las de
OperadorB y OperadorC se crean recién cuando el negocio confirme sus URLs
y credenciales por sociedad.

## Cómo arrancar (una vez cerrados los pendientes)

1. Completar los pendientes de `Config.xlsx` listados arriba.
2. Confirmar `config/RutaArchivoConfig.txt` con la ruta real donde
   vivirá `Config.xlsx` en la máquina del robot.
3. Correr los diagnósticos pendientes contra los portales reales y
   confirmar selectores.
4. Construir, un módulo a la vez, la lógica dentro de
   `_ejecutar_flujo_principal()` en `main.py` (login por portal →
   descarga → cruce → carga SAP → notificación), probando cada pieza
   aislada antes de integrarla.

## Instalación

```powershell
py -m pip install -r requirements.txt
py -m playwright install chromium
```

Confirma también que el driver correspondiente a tu base de datos esté
instalado ("ODBC Driver 18 for SQL Server" -- driver de Windows
aparte, no algo que instale `pip`).
