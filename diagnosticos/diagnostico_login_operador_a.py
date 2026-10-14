"""
Script de diagnostico -- SOLO LECTURA, sin credenciales.

Que hace: abre la pagina publica de login de OperadorA
(https://portal.operador-a.example/auth/login -- confirmada como la
URL vigente; la que trae el ENT es de la plataforma anterior), y vuelca
la estructura real del formulario: campos (usuario, contrasena),
botones, e iframes (el reCAPTCHA normalmente vive en uno). No escribe
nada en la pagina, no ingresa ningun usuario/contrasena, no hace click
en nada.

Por que hace falta: no se puede automatizar de forma confiable un
formulario adivinando los selectores (id/name de los campos) -- hay
que verlos tal cual los entrega el sitio real. Ver la guia
metodologica, seccion 4, paso 2.

Por que NO usa config/config_reader.py todavia: cargar_configuracion()
valida TODO Config.xlsx de una sola vez (incluye DataBase.TablaPrincipal
y las sociedades de OperadorC, que todavia estan pendientes de definir) --
este script solo necesita la URL de OperadorA, asi que por ahora la trae
fija (hardcodeada) en vez de depender de que el resto del Excel ya
este completo. Cuando el modulo de login real de OperadorA exista en
proceso/descargas/operador_a/, ese si va a leer todo desde Configuracion
(config.obtener_operador("OPERADOR_A").link), como el resto del robot.

Como correrlo:
    pip install playwright
    playwright install chromium
    python diag_login.py

Que hacer con el resultado:
    Se genera, en la misma carpeta de este script:
      - resultado.json       -> estructura del formulario en texto
      - login_screenshot.png -> captura de la pagina tal como cargo

    Pega de vuelta el CONTENIDO de resultado.json (como texto, no
    como adjunto -- ver la guia metodologica, seccion 3, sobre por
    que el texto plano funciona mejor que adjuntar archivos largos),
    y sube tambien login_screenshot.png.
"""
from pathlib import Path
import json

from playwright.sync_api import sync_playwright

URL = "https://portal.operador-a.example/auth/login"
CARPETA_SALIDA = Path(__file__).resolve().parent


def dump_element(el):
    try:
        tag = el.evaluate("e => e.tagName")
        attrs = el.evaluate(
            "e => Object.fromEntries([...e.attributes].map(a => [a.name, a.value]))"
        )
        visible = el.is_visible()
        return {"tag": tag, "attrs": attrs, "visible": visible}
    except Exception as e:
        return {"error": str(e)}


def main():
    with sync_playwright() as p:
        # headless=False si quieres ver el navegador abrirse en tu pantalla
        # mientras corre -- util para confirmar visualmente que cargo bien.
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        result = {"url_solicitada": URL}
        try:
            resp = page.goto(URL, timeout=45000, wait_until="domcontentloaded")
            result["status_http"] = resp.status if resp else None
            page.wait_for_timeout(4000)  # deja tiempo a que cargue el recaptcha (JS async)
            result["url_final"] = page.url
            result["titulo"] = page.title()

            inputs = page.query_selector_all("input")
            result["inputs"] = [dump_element(i) for i in inputs]

            buttons = page.query_selector_all("button")
            result["buttons"] = [dump_element(b) for b in buttons]

            enlaces_relevantes = page.query_selector_all("a")
            result["enlaces"] = [
                dump_element(a) for a in enlaces_relevantes
                if "contrase" in (a.inner_text() or "").lower()
                or "olvid" in (a.inner_text() or "").lower()
            ]

            frames = page.frames
            result["iframes"] = [
                {"name": f.name, "url": f.url} for f in frames if f != page.main_frame
            ]

            ruta_captura = CARPETA_SALIDA / "login_screenshot.png"
            page.screenshot(path=str(ruta_captura), full_page=True)
            result["screenshot"] = str(ruta_captura)

        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

        ruta_resultado = CARPETA_SALIDA / "resultado.json"
        ruta_resultado.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
