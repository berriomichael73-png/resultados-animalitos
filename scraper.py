import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Importación de nuevos módulos
try:
    from modulo_telegram import obtener_resultados_telegram
except ImportError:
    obtener_resultados_telegram = None

try:
    from modulo_live_stream import analizar_frame_transmision
except ImportError:
    analizar_frame_transmision = None

LOTERIAS_OFICIALES = {
    "Lotto Activo": {"slugs": ["lotto-activo"], "tuazar": "lotto-activo", "logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"slugs": ["la-granjita"], "tuazar": "la-granjita", "logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje Millonario)": {"slugs": ["monje-millonario"], "tuazar": "monje-millonario", "logo": "https://loteriadehoy.com/images/monje-millonario.png"},
    "Guacharo Activo": {"slugs": ["guacharo-activo"], "tuazar": "guacharo-activo", "logo": "https://loteriadehoy.com/images/guacharo-activo.png"},
    "El Guacharito Millonario": {"slugs": ["el-guacharito-millonario"], "tuazar": "el-guacharito-millonario", "logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png"},
    "Selva Plus": {"slugs": ["selva-plus"], "tuazar": "selva-plus", "logo": "https://loteriadehoy.com/images/selva-plus.png"},
    "Centena Plus": {"slugs": ["centena-plus"], "tuazar": "centena-plus", "logo": "https://loteriadehoy.com/images/centena-plus.png"},
    "Lotto Activo Rd Int": {"slugs": ["lotto-activo-rd-int"], "tuazar": "lotto-activo-rd-int", "logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png"},
    "Mega Animal 40": {"slugs": ["mega-animal-40"], "tuazar": "mega-animal-40", "logo": "https://loteriadehoy.com/images/mega-animal-40.png"},
    "Centena Animalitos": {"slugs": ["centena-animalitos"], "tuazar": "centena-animalitos", "logo": "https://loteriadehoy.com/images/centena-animalitos.png"},
    "Chance Con Animalitos": {"slugs": ["chance-con-animalitos"], "tuazar": "chance-con-animalitos", "logo": "https://loteriadehoy.com/images/chance-con-animalitos.png"},
    "Cazaloton": {"slugs": ["cazaloton"], "tuazar": "cazaloton", "logo": "https://loteriadehoy.com/images/cazaloton.png"},
    "Ruleta Activa": {"slugs": ["ruleta-activa"], "tuazar": "ruleta-activa", "logo": "https://loteriadehoy.com/images/ruleta-activa.png"},
    "Granja Millonaria": {"slugs": ["granja-millonaria"], "tuazar": "granja-millonaria", "logo": "https://loteriadehoy.com/images/granja-millonaria.png"},
    "La-Ricachona": {"slugs": ["la-ricachona"], "tuazar": "la-ricachona", "logo": "https://loteriadehoy.com/images/la-ricachona.png"},
    "Jungla Millonaria": {"slugs": ["jungla-millonaria"], "tuazar": "jungla-millonaria", "logo": "https://loteriadehoy.com/images/jungla-millonaria.png"},
    "Loto Chaima": {"slugs": ["loto-chaima"], "tuazar": "loto-chaima", "logo": "https://loteriadehoy.com/images/loto-chaima.png"},
    "Lotto Activo RDominicana": {"slugs": ["lotto-activo-rdominicana"], "tuazar": "lotto-activo-rdominicana", "logo": "https://loteriadehoy.com/images/lotto-activo-rdominicana.png"}
}

HORARIOS_ORDENADOS = [
    ("08:00 AM", 8.0), ("09:00 AM", 9.0), ("10:00 AM", 10.0), ("11:00 AM", 11.0),
    ("12:00 PM", 12.0), ("01:00 PM", 13.0), ("02:00 PM", 14.0), ("03:00 PM", 15.0),
    ("04:00 PM", 16.0), ("05:00 PM", 17.0), ("06:00 PM", 18.0), ("07:00 PM", 19.0)
]

PROXY_URL = os.getenv("PROXY_URL", "")

def obtener_fecha_venezuela():
    tz_ve = timezone(timedelta(hours=-4))
    return datetime.now(tz_ve).strftime("%Y-%m-%d")

def escanear_sistema_completo(browser):
    resultados_totales = []

    # 1. Intentar extracción por Redes Sociales / Telegram (Opción 3)
    datos_telegram = obtener_resultados_telegram() if obtener_resultados_telegram else []

    context_args = {
        "user_agent": "Mozilla/5.0 (Linux; Android 10; Redmi Note 9 Pro) AppleWebKit/537.36",
        "viewport": {"width": 412, "height": 915},
        "is_mobile": True
    }
    if PROXY_URL:
        context_args["proxy"] = {"server": PROXY_URL}

    context = browser.new_context(**context_args)
    page = context.new_page()
    page.route("**/*.{css,woff,woff2}", lambda route: route.abort())

    for loteria_nombre, info in LOTERIAS_OFICIALES.items():
        slugs = info["slugs"]
        logo_loteria = info["logo"]
        sorteos_obtenidos = {}

        # Mapear datos de Telegram si existen para esta lotería
        for dt in datos_telegram:
            if dt.get("loteria") == loteria_nombre:
                sorteos_obtenidos[dt["hora"]] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": logo_loteria,
                    "hora": dt["hora"],
                    "numero": dt["numero"],
                    "animal": dt["animal"],
                    "imagen": "",
                    "realizado": True
                }

        # 2. Si faltan datos, realizar Scraping con Failover (Opción 4)
        if not sorteos_obtenidos:
            for slug in slugs:
                urls_prueba = [
                    f"https://www.tuazar.com/triples/animalitos/{info['tuazar']}/",
                    f"https://loteriadehoy.com/animalitos/{slug}"
                ]

                for url_target in urls_prueba:
                    try:
                        page.goto(url_target, wait_until="domcontentloaded", timeout=10000)
                        page.wait_for_timeout(1000)
                        html = page.content()
                        soup = BeautifulSoup(html, "html.parser")

                        bloques = soup.find_all(["tr", "div", "li", "article", "td"])
                        for bloque in bloques:
                            txt_bloque = bloque.get_text(" ", strip=True)
                            if len(txt_bloque) > 300:
                                continue

                            match_hora = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', txt_bloque)
                            if not match_hora:
                                continue
                            
                            hora_det = match_hora.group(1).upper()
                            if hora_det in sorteos_obtenidos:
                                continue

                            img_tag = bloque.find("img")
                            if img_tag:
                                src = img_tag.get("src", "")
                                if src and not ("logo" in src.lower() or "icon" in src.lower()):
                                    if not src.startswith("http"):
                                        src = "https://www.tuazar.com" if "tuazar" in url_target else "https://loteriadehoy.com"
                                        src = src + (src_img if (src_img := img_tag.get("src")).startswith("/") else "/" + src_img)

                                    match_num = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src.lower())
                                    numero = match_num.group(1).zfill(2) if match_num else "--"
                                    animal = img_tag.get("alt") or img_tag.get("title") or "Animalito"

                                    sorteos_obtenidos[hora_det] = {
                                        "loteria": loteria_nombre,
                                        "logo_loteria": logo_loteria,
                                        "hora": hora_det,
                                        "numero": numero,
                                        "animal": animal.strip(),
                                        "imagen": src,
                                        "realizado": True
                                    }

                        if sorteos_obtenidos:
                            break
                    except Exception:
                        continue

                if sorteos_obtenidos:
                    break

        # Rellenar casillas de horarios faltantes
        for h_estandar, _ in HORARIOS_ORDENADOS:
            if h_estandar not in sorteos_obtenidos:
                sorteos_obtenidos[h_estandar] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": logo_loteria,
                    "hora": h_estandar,
                    "numero": "--",
                    "animal": "Por salir",
                    "imagen": "",
                    "realizado": False
                }

        for h_estandar, _ in HORARIOS_ORDENADOS:
            if h_estandar in sorteos_obtenidos:
                resultados_totales.append(sorteos_obtenidos[h_estandar])

    context.close()
    return resultados_totales

def ejecutar_proceso():
    hoy_str = obtener_fecha_venezuela()

    historial = {}
    if os.path.exists("historial_resultados.json"):
        try:
            with open("historial_resultados.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        lista_resultados_dia = escanear_sistema_completo(browser)

        for item in lista_resultados_dia:
            item["fecha"] = hoy_str

        with open("resultados.json", "w", encoding="utf-8") as f:
            json.dump(lista_resultados_dia, f, ensure_ascii=False, indent=2)

        historial[hoy_str] = lista_resultados_dia
        with open("historial_resultados.json", "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)

        browser.close()

if __name__ == "__main__":
    ejecutar_proceso()
    print("Sincronización multi-fuente total (Opciones 1, 3 y 4) completada.")
