import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

LOTERIAS_OFICIALES = {
    "Lotto Activo": {"slugs": ["lotto-activo"], "tuazar": "lotto-activo", "logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"slugs": ["la-granjita"], "tuazar": "la-granjita", "logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje Millonario)": {"slugs": ["monje-millonario", "lotto-activo-2"], "tuazar": "monje-millonario", "logo": "https://loteriadehoy.com/images/monje-millonario.png"},
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

def intentar_obtencion_api_directa(slugs):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi Note 9 Pro) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    for slug in slugs:
        urls_api = [
            f"https://loteriadehoy.com/api/v1/animalitos/{slug}",
            f"https://m.parley.la/api/resultados/resultados-{slug}",
            f"https://lotoven.com/api/v1/resultados/{slug}"
        ]
        for url in urls_api:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if data and isinstance(data, list):
                        return data
            except Exception:
                continue
    return None

def extraer_hora_de_texto(texto):
    match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', texto)
    if match:
        hora_str = match.group(1).strip().upper()
        if "AM" not in hora_str and "PM" not in hora_str:
            h_num = int(hora_str.split(":")[0])
            hora_str += " PM" if h_num in [12, 1, 2, 3, 4, 5, 6, 7] else " AM"
        return hora_str
    return None

def escanear_hibrido_multi_fuente(browser):
    resultados_totales = []

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

        # 1. Capa API
        datos_api = intentar_obtencion_api_directa(slugs)
        if datos_api:
            for item in datos_api:
                hora_item = item.get("hora", "08:00 AM")
                num_item = str(item.get("numero", "--")).zfill(2)
                img_item = item.get("imagen", "")
                nom_item = item.get("animal", "Animalito")
                
                if img_item and not img_item.startswith("http"):
                    img_item = "https://loteriadehoy.com" + (img_item if img_item.startswith("/") else "/" + img_item)

                sorteos_obtenidos[hora_item] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": logo_loteria,
                    "hora": hora_item,
                    "numero": num_item,
                    "animal": nom_item,
                    "imagen": img_item,
                    "realizado": True if num_item != "--" else False
                }

        # 2. Capa Playwright (loteriadehoy.com / tuazar.com)
        if not sorteos_obtenidos:
            for slug in slugs:
                urls_prueba = [
                    f"https://loteriadehoy.com/animalitos/{slug}",
                    f"https://m.parley.la/resultados/resultados-{slug}",
                    f"https://www.tuazar.com/triples/animalitos/{info['tuazar']}/"
                ]

                for url_target in urls_prueba:
                    try:
                        page.goto(url_target, wait_until="networkidle", timeout=12000)
                        page.wait_for_timeout(1000)
                        html = page.content()
                        soup = BeautifulSoup(html, "html.parser")

                        bloques = soup.find_all(["tr", "div", "li", "article", "td"])
                        for bloque in bloques:
                            txt_bloque = bloque.get_text(" ", strip=True)
                            if len(txt_bloque) > 300:
                                continue

                            hora_detectada = extraer_hora_de_texto(txt_bloque)
                            if not hora_detectada or hora_detectada in sorteos_obtenidos:
                                continue

                            img_tag = bloque.find("img")
                            if img_tag:
                                src = img_tag.get("src", "")
                                if src and not ("logo" in src.lower() or "icon" in src.lower()):
                                    if not src.startswith("http"):
                                        src = "https://loteriadehoy.com" + (src if src.startswith("/") else "/" + src)

                                    match_num = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src.lower())
                                    numero = match_num.group(1).zfill(2) if match_num else "--"
                                    animal = img_tag.get("alt") or img_tag.get("title") or "Animalito"

                                    sorteos_obtenidos[hora_detectada] = {
                                        "loteria": loteria_nombre,
                                        "logo_loteria": logo_loteria,
                                        "hora": hora_detectada,
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

        # 3. Rellenar estructura de horarios
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
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        lista_resultados_dia = escanear_hibrido_multi_fuente(browser)

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
    print("Sincronización robusta multifuente completada.")
