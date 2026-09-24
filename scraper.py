import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Mapeo de loterías con sus fuentes y slugs oficiales prioritarios
LOTERIAS_OFICIALES = {
    "Lotto Activo": {
        "slug": "lotto-activo",
        "url_oficial": "https://lottoactivo.com/resultados/",
        "api_oficial": "https://api.lottoactivo.com/v1/resultados"
    },
    "La Granjita": {
        "slug": "la-granjita",
        "url_oficial": "https://lagranjitaonline.com/resultados/",
        "api_oficial": "https://api.lagranjitaonline.com/v1/resultados"
    },
    "Lotto Activo 2 (Monje Millonario)": {
        "slug": "monje-millonario",
        "url_oficial": "https://loteriadehoy.com/animalitos/monje-millonario",
        "api_oficial": None
    },
    "Guacharo Activo": {
        "slug": "guacharo-activo",
        "url_oficial": "https://guacharoactivo.com/resultados/",
        "api_oficial": None
    },
    "El Guacharito Millonario": {
        "slug": "el-guacharito-millonario",
        "url_oficial": "https://loteriadehoy.com/animalitos/el-guacharito-millonario",
        "api_oficial": None
    },
    "Selva Plus": {
        "slug": "selva-plus",
        "url_oficial": "https://selvaplus.com/resultados/",
        "api_oficial": None
    },
    "Centena Plus": {
        "slug": "centena-plus",
        "url_oficial": "https://loteriadehoy.com/animalitos/centena-plus",
        "api_oficial": None
    },
    "Lotto Activo Rd Int": {
        "slug": "lotto-activo-rd-int",
        "url_oficial": "https://loteriadehoy.com/animalitos/lotto-activo-rd-int",
        "api_oficial": None
    },
    "Mega Animal 40": {
        "slug": "mega-animal-40",
        "url_oficial": "https://loteriadehoy.com/animalitos/mega-animal-40",
        "api_oficial": None
    },
    "Centena Animalitos": {
        "slug": "centena-animalitos",
        "url_oficial": "https://loteriadehoy.com/animalitos/centena-animalitos",
        "api_oficial": None
    },
    "Chance Con Animalitos": {
        "slug": "chance-con-animalitos",
        "url_oficial": "https://loteriadehoy.com/animalitos/chance-con-animalitos",
        "api_oficial": None
    },
    "Cazaloton": {
        "slug": "cazaloton",
        "url_oficial": "https://cazaloton.com/resultados/",
        "api_oficial": None
    },
    "Ruleta Activa": {
        "slug": "ruleta-activa",
        "url_oficial": "https://ruletaactiva.com/resultados/",
        "api_oficial": None
    },
    "Granja Millonaria": {
        "slug": "granja-millonaria",
        "url_oficial": "https://loteriadehoy.com/animalitos/granja-millonaria",
        "api_oficial": None
    },
    "La-Ricachona": {
        "slug": "la-ricachona",
        "url_oficial": "https://loteriadehoy.com/animalitos/la-ricachona",
        "api_oficial": None
    },
    "Jungla Millonaria": {
        "slug": "jungla-millonaria",
        "url_oficial": "https://loteriadehoy.com/animalitos/jungla-millonaria",
        "api_oficial": None
    },
    "Loto Chaima": {
        "slug": "loto-chaima",
        "url_oficial": "https://loteriadehoy.com/animalitos/loto-chaima",
        "api_oficial": None
    },
    "Lotto Activo RDominicana": {
        "slug": "lotto-activo-rdominicana",
        "url_oficial": "https://loteriadehoy.com/animalitos/lotto-activo-rdominicana",
        "api_oficial": None
    }
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

# SOLUCIÓN DEFINITIVA 1: API DIRECTA MULTI-FUENTE
def intentar_obtencion_api_directa(info_loteria):
    urls_api = []
    if info_loteria.get("api_oficial"):
        urls_api.append(info_loteria["api_oficial"])
    
    slug = info_loteria["slug"]
    urls_api.extend([
        f"https://loteriadehoy.com/api/v1/animalitos/{slug}",
        f"https://m.parley.la/api/resultados/{slug}",
        f"https://lotoven.com/api/v1/resultados/{slug}"
    ])

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

def extraer_datos_directos(contenedor, url_base):
    for img in contenedor.find_all("img"):
        src = img.get("src", "")
        if src:
            if not src.startswith("http"):
                src = url_base.rstrip("/") + ("/" if not src.startswith("/") else "") + src

            match_num = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src.lower())
            numero = match_num.group(1).zfill(2) if match_num else "--"
            nombre = img.get("alt") or img.get("title") or "Resultado"
            return {"numero": numero, "animal": nombre.strip(), "imagen": src}

    return None

def escanear_hibrido_multi_sitio(browser):
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

    for loteria_nombre, info in LOTERIAS_OFICIALES.items():
        # CAPA 1: API Directa
        datos_api = intentar_obtencion_api_directa(info)
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

        # CAPA 2: Scraper Híbrido con Proxy Residencial directo al sitio oficial
        url_destino = info["url_oficial"]
        try:
            page.goto(url_destino, wait_until="domcontentloaded", timeout=12000)
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
                        res = extraer_datos_directos(el, url_destino)
                        if res:
                            datos_extraidos[clave] = res

        except Exception as e:
            print(f"Error procesando {loteria_nombre} en sitio oficial: {e}")
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

        mapa_extraido_dia = escanear_hibrido_multi_sitio(browser)
        resultados_fecha = []

        for loteria_nombre in LOTERIAS_OFICIALES.keys():
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
    print("Sincronización multi-fuente desde páginas oficiales completada con éxito.")
