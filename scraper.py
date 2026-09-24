import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Mapeo exacto de las loterías visibles en loteriadehoy.com
LOTERIAS_MAPA = {
    "Lotto Activo": "lotto-activo",
    "La Granjita": "la-granjita",
    "Lotto Activo 2 (Monje Millonario)": "monje-millonario",
    "Guacharo Activo": "guacharo-activo",
    "El Guacharito Millonario": "el-guacharito-millonario",
    "Selva Plus": "selva-plus",
    "Centena Plus": "centena-plus",
    "Lotto Activo Rd Int": "lotto-activo-rd-int",
    "Mega Animal 40": "mega-animal-40",
    "Centena Animalitos": "centena-animalitos",
    "Chance Con Animalitos": "chance-con-animalitos",
    "Cazaloton": "cazaloton",
    "Ruleta Activa": "ruleta-activa",
    "Granja Millonaria": "granja-millonaria",
    "La-Ricachona": "la-ricachona",
    "Jungla Millonaria": "jungla-millonaria",
    "Loto Chaima": "loto-chaima",
    "Lotto Activo RDominicana": "lotto-activo-rdominicana"
}

HORARIOS_EN_PUNTO = [
    ("08:00 AM", 8.0), ("09:00 AM", 9.0), ("10:00 AM", 10.0), ("11:00 AM", 11.0),
    ("12:00 PM", 12.0), ("01:00 PM", 13.0), ("02:00 PM", 14.0), ("03:00 PM", 15.0),
    ("04:00 PM", 16.0), ("05:00 PM", 17.0), ("06:00 PM", 18.0), ("07:00 PM", 19.0)
]

HORARIOS_MEDIAS_HORAS = [
    ("08:30 AM", 8.5), ("09:30 AM", 9.5), ("10:30 AM", 10.5), ("11:30 AM", 11.5),
    ("12:30 PM", 12.5), ("01:30 PM", 13.5), ("02:30 PM", 14.5), ("03:30 PM", 15.5),
    ("04:30 PM", 16.5), ("05:30 PM", 17.5), ("06:30 PM", 18.5), ("07:30 PM", 19.5)
]

TODOS_LOS_HORARIOS = sorted(HORARIOS_EN_PUNTO + HORARIOS_MEDIAS_HORAS, key=lambda x: x[1])

# SOLUCIÓN DEFINITIVA 2: PROXY RESIDENCIAL
PROXY_URL = os.getenv("PROXY_URL", "")

# SOLUCIÓN DEFINITIVA 1: API DIRECTA
def intentar_obtencion_api_directa(slug):
    urls_api = [
        f"https://loteriadehoy.com/api/v1/animalitos/{slug}",
        f"https://m.parley.la/api/resultados/{slug}"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi Note 9 Pro) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    for url in urls_api:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and isinstance(data, list):
                    return data
        except Exception:
            continue
    return None

def extraer_datos_directos(contenedor):
    for img in contenedor.find_all("img"):
        src = img.get("src", "")
        if src:
            if not src.startswith("http"):
                src = "https://loteriadehoy.com" + (src if src.startswith("/") else "/" + src)

            match_num = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src.lower())
            numero = match_num.group(1).zfill(2) if match_num else "--"
            nombre = img.get("alt") or img.get("title") or "Resultado"
            return {"numero": numero, "animal": nombre.strip(), "imagen": src}

    return None

def escanear_hibrido(browser):
    datos_extraidos = {}

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

    for loteria_nombre, slug in LOTERIAS_MAPA.items():
        # CAPA 1: Intento por API Directa
        datos_api = intentar_obtencion_api_directa(slug)
        if datos_api:
            for item in datos_api:
                hora_item = item.get("hora")
                num_item = str(item.get("numero", "")).zfill(2)
                img_item = item.get("imagen", "")
                nom_item = item.get("animal", "Resultado")
                
                if hora_item:
                    datos_extraidos[f"{loteria_nombre}-{hora_item}"] = {
                        "numero": num_item,
                        "animal": nom_item,
                        "imagen": img_item
                    }
            continue

        # CAPA 2: Scraper Híbrido con Proxy Residencial en loteriadehoy.com
        url = f"https://loteriadehoy.com/animalitos/{slug}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(1000)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            elementos = soup.find_all(["tr", "div", "li", "article", "td"])
            for el in elementos:
                txt_el = el.get_text(" ", strip=True)
                if len(txt_el) > 300:
                    continue

                for hora_std, _ in TODOS_LOS_HORARIOS:
                    clave = f"{loteria_nombre}-{hora_std}"
                    if clave in datos_extraidos:
                        continue

                    hora_base = hora_std.split()[0]
                    if hora_base in txt_el or hora_std.lower() in txt_el.lower():
                        res = extraer_datos_directos(el)
                        if res:
                            datos_extraidos[clave] = res

        except Exception as e:
            print(f"Error procesando {loteria_nombre}: {e}")
            continue

    context.close()
    return datos_extraidos

def ejecutar_proceso():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour + (hoy_dt.minute / 60.0)

    hora_ultimo_sorteo = "08:00 AM"
    for h_txt, h_val in TODOS_LOS_HORARIOS:
        if h_val <= hora_actual_ve:
            hora_ultimo_sorteo = h_txt

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

        mapa_extraido_dia = escanear_hibrido(browser)
        resultados_fecha = []

        for loteria_nombre in LOTERIAS_MAPA.keys():
            for hora_texto, hora_val in TODOS_LOS_HORARIOS:
                ha_ocurrido = (hora_val <= hora_actual_ve)
                clave = f"{loteria_nombre}-{hora_texto}"

                if ha_ocurrido and clave in mapa_extraido_dia:
                    info = mapa_extraido_dia[clave]
                    num_str = info["numero"]
                    nombre_animal = info["animal"]
                    imagen_url = info["imagen"]
                    realizado = True
                else:
                    num_str = "--"
                    nombre_animal = "Por salir"
                    imagen_url = ""
                    realizado = False

                resultados_fecha.append({
                    "fecha": hoy_str,
                    "loteria": loteria_nombre,
                    "hora": hora_texto,
                    "hora_num": hora_val,
                    "numero": num_str,
                    "animal": nombre_animal,
                    "imagen": imagen_url,
                    "realizado": realizado,
                    "es_ultimo_en_vivo": (hora_texto == hora_ultimo_sorteo)
                })

        historial[hoy_str] = resultados_fecha

        with open("resultados.json", "w", encoding="utf-8") as f:
            json.dump(resultados_fecha, f, ensure_ascii=False, indent=2)

        browser.close()

    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ejecutar_proceso()
    print("Sincronización desde loteriadehoy.com completada con éxito.")
