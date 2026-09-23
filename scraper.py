import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

nombres_animales = {
    "00": "Delfín", "0": "Delfín", "1": "Carnero", "01": "Carnero", "2": "Toro", "02": "Toro",
    "3": "Ciempiés", "03": "Ciempiés", "4": "Escorpión", "04": "Escorpión", "5": "León", "05": "León",
    "6": "Rana", "06": "Rana", "7": "Perico", "07": "Perico", "8": "Ratón", "08": "Ratón",
    "9": "Águila", "09": "Águila", "10": "Tigre", "11": "Gato", "12": "Caballo", "13": "Mono",
    "14": "Paloma", "15": "Zorro", "16": "Oso", "17": "Pavo", "18": "Burro", "19": "Chivo",
    "20": "Cochino", "21": "Gallo", "22": "Camello", "23": "Cebra", "24": "Iguana", "25": "Gallina",
    "26": "Vaca", "27": "Perro", "28": "Zamuro", "29": "Elefante", "30": "Caimán", "31": "Lapa",
    "32": "Ardilla", "33": "Pescado", "34": "Venado", "35": "Jirafa", "36": "Culebra", "37": "Abeja",
    "38": "Erizo", "39": "Flamenco", "40": "Foca", "41": "Canguro", "42": "Perezoso", "43": "Zorrillo",
    "44": "Nutria", "45": "Tejón", "46": "Mamut", "47": "Dodo", "48": "Pavo Real", "49": "Búho",
    "50": "Murciélago", "51": "Medusa", "52": "Pulpo", "53": "Langosta", "54": "Cangrejo", "55": "Ostra",
    "56": "Mariposa", "57": "Hormiga", "58": "Mariquita", "59": "Grillo", "60": "Araña", "61": "Gato",
    "62": "Perro", "63": "Caballo", "64": "Toro", "65": "León", "66": "Tigre", "67": "Gallo",
    "68": "Pescado", "69": "Caimán", "70": "Elefante", "71": "Zamuro", "72": "Lapa", "73": "Ardilla",
    "74": "Venado", "75": "Jirafa", "76": "Culebra", "77": "Abeja", "78": "Erizo", "79": "Flamenco",
    "80": "Foca", "81": "Canguro", "82": "Perezoso", "83": "Zorrillo", "84": "Nutria", "85": "Tejón",
    "86": "Mamut", "87": "Dodo", "88": "Pavo Real", "89": "Búho", "90": "Murciélago", "91": "Medusa",
    "92": "Pulpo", "93": "Langosta", "94": "Cangrejo", "95": "Ostra", "96": "Mariposa", "97": "Hormiga",
    "98": "Mariquita", "99": "Grillo"
}

# Slugs mapeados para Lotoven
LOTERIAS_LOTOVEN = {
    "Lotto Activo": "lotto-activo",
    "Ruleta Activa": "ruleta-activa",
    "La Ruca": "la-ruca",
    "Lotto Activo Internacional": "lotto-activo-internacional",
    "TrioActivo": "trioactivo",
    "Guacharo Activo": "guacharo-activo",
    "Selva Plus": "selva-plus",
    "El Ruco": "el-ruco",
    "Chance Animalitos": "chance-con-animalitos",
    "Lotto Rey": "lotto-rey",
    "Ruleta Royal": "ruleta-royal",
    "Loto Chaima": "loto-chaima",
    "Cazaloton": "cazaloton",
    "Panda Plus": "panda-plus",
    "Mega Animal40": "mega-animal-40",
    "Lotto Gato": "lotto-gato",
    "Gatazo": "gatazo",
    "Tigre Millonario": "tigre-millonario",
    "Guacharito Millonario": "el-guacharito-millonario",
    "Centena Animalitos": "centena-animalitos",
    "Centena Plus": "centena-plus",
    "Triple Centena": "triple-centena",
    "Lotto Max": "lotto-max",
    "Granja Millonaria Animalitos": "granja-millonaria",
    "Granja Millonaria Granjazo": "granjazo",
    "Lotto Pantera": "lotto-pantera",
    "Lotoanimalito": "lotoanimalito",
    "Triple Pantera": "triple-pantera"
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

def extraer_animalito(contenedor):
    for img in contenedor.find_all("img"):
        src = img.get("src", "").lower()
        alt = img.get("alt", "").lower()
        title = img.get("title", "").lower()
        comb = f"{src} {alt} {title}"

        for num_code, anim_nombre in nombres_animales.items():
            if anim_nombre.lower() in comb:
                return num_code.zfill(2)

        match_img = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src)
        if match_img:
            num_cand = match_img.group(1).zfill(2)
            if num_cand in nombres_animales:
                return num_cand

    txt = contenedor.get_text(" ", strip=True)
    for num_code, anim_nombre in nombres_animales.items():
        if anim_nombre.lower() in txt.lower():
            return num_code.zfill(2)

    return None

def escanear_lotoven(page):
    datos_extraidos = {}

    for loteria_nombre, slug in LOTERIAS_LOTOVEN.items():
        url = f"https://lotoven.com/resultados/{slug}/"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(800)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            elementos = soup.find_all(["tr", "div", "li", "article", "td"])
            for el in elementos:
                txt_el = el.get_text(" ", strip=True)
                if len(txt_el) > 250:
                    continue

                for hora_std, _ in TODOS_LOS_HORARIOS:
                    clave = f"{loteria_nombre}-{hora_std}"
                    if clave in datos_extraidos:
                        continue

                    hora_num = hora_std[:2]
                    hora_alt = str(int(hora_num))
                    minutos = "30" if ":30" in hora_std else "00"

                    patron_hora = f"{hora_num}:{minutos}"
                    patron_alt = f"{hora_alt}:{minutos}"

                    if patron_hora in txt_el or patron_alt in txt_el:
                        res = extraer_animalito(el)
                        if res:
                            datos_extraidos[clave] = res

        except Exception as e:
            print(f"Error procesando {loteria_nombre} en Lotoven: {e}")
            continue

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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Linux; Android 10; Redmi Note 9 Pro) AppleWebKit/537.36")
        page = context.new_page()

        # Bloquear assets pesados para mayor velocidad
        page.route("**/*.{png,jpg,jpeg,webp,svg,css,woff,woff2}", lambda route: route.abort())

        mapa_extraido_dia = escanear_lotoven(page)
        resultados_fecha = []

        for loteria_nombre in LOTERIAS_LOTOVEN.keys():
            for hora_texto, hora_val in TODOS_LOS_HORARIOS:
                ha_ocurrido = (hora_val <= hora_actual_ve)
                clave = f"{loteria_nombre}-{hora_texto}"

                if ha_ocurrido and clave in mapa_extraido_dia:
                    num_str = mapa_extraido_dia[clave]
                    nombre_animal = nombres_animales.get(num_str, "Animal")
                    realizado = True
                else:
                    num_str = "--"
                    nombre_animal = "Por salir"
                    realizado = False

                resultados_fecha.append({
                    "fecha": hoy_str,
                    "loteria": loteria_nombre,
                    "hora": hora_texto,
                    "hora_num": hora_val,
                    "numero": num_str,
                    "animal": nombre_animal,
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
    print("Sincronización completa desde Lotoven completada.")
