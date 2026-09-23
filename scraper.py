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
    "56": "Mariposa", "57": "Hormiga", "58": "Mariquita", "59": "Grillo", "60": "Araña"
}

LOTERIAS_PARLEY = {
    "Lotto Activo": "lotto-activo",
    "La Granjita": "la-granjita",
    "Ruleta Activa": "ruleta-activa",
    "Lotto Rey": "lotto-rey",
    "Lotto Activo RD": "lotto-activo-rd",
    "Granjita Plus": "la-granjita-plus",
    "Ruleta Royal": "ruleta-royal",
    "Guácharo Activo": "el-guacharo-activo",
    "Selva Plus": "selva-plus",
    "Chance Animal": "chance-animal",
    "Tropi Gana": "tropigana",
    "Lotto Zoo": "lotto-zoo",
    "Tropicana Animal": "tropicana-animal",
    "Gana Animalito": "gana-animalito",
    "Súper Gana": "super-gana",
    "Sorteo VIP": "sorteo-vip",
    "Animalitos Millonarios": "animalitos-millonarios",
    "Lotto Venezuela": "lotto-venezuela"
}

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def extraer_animalito_parley(contenedor):
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

def escanear_tanda_parley(browser, lote_loterias, fecha_str):
    datos_lote = {}
    
    # Crear un contexto nuevo (pestaña/sesión limpia) por cada grupo de 3
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    )
    page = context.new_page()

    for loteria_nombre, slug in lote_loterias:
        url = f"https://m.parley.la/resultados/resultados-{slug}"
        if fecha_str:
            url += f"/{fecha_str}"

        try:
            page.goto(url, timeout=25000)
            page.wait_for_timeout(2500)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            elementos = soup.find_all(["tr", "div", "li", "article"])
            for el in elementos:
                txt_el = el.get_text(" ", strip=True)
                for hora_std, _ in HORARIOS:
                    clave = f"{loteria_nombre}-{hora_std}"
                    if clave in datos_lote:
                        continue

                    hora_num = hora_std[:2]
                    hora_alt = str(int(hora_num))
                    
                    if f"{hora_num}:00" in txt_el or f"{hora_alt}:00" in txt_el:
                        res = extraer_animalito_parley(el)
                        if res:
                            datos_lote[clave] = res

        except Exception as e:
            print(f"Error procesando {loteria_nombre} en Parley: {e}")
            continue

        time.sleep(1)  # Pausa breve entre páginas del mismo lote

    context.close()
    return datos_lote

def ejecutar_proceso_parley():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour
    minuto_actual_ve = hoy_dt.minute

    fechas_a_procesar = [(hoy_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
    
    historial = {}
    if os.path.exists("historial_resultados.json"):
        try:
            with open("historial_resultados.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    items_loterias = list(LOTERIAS_PARLEY.items())
    
    # Dividir las 18 loterías en tandas estrictas de 3 en 3
    tandas = [items_loterias[i:i + 3] for i in range(0, len(items_loterias), 3)]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for fecha_str in fechas_a_procesar:
            es_hoy = (fecha_str == hoy_str)
            fecha_param = "" if es_hoy else fecha_str
            
            mapa_extraido_dia = {}

            # Ejecutar escaneo por cada tanda de 3 loterías
            for tanda in tandas:
                datos_tanda = escanear_tanda_parley(browser, tanda, fecha_param)
                mapa_extraido_dia.update(datos_tanda)
                time.sleep(2)  # Pausa de seguridad entre tandas

            resultados_fecha = []

            for loteria_nombre, _ in items_loterias:
                for hora_texto, hora_num in HORARIOS:
                    ha_ocurrido = True
                    if es_hoy:
                        if hora_num > hora_actual_ve:
                            ha_ocurrido = False
                        elif hora_num == hora_actual_ve and minuto_actual_ve < 2:
                            ha_ocurrido = False

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
                        "fecha": fecha_str,
                        "loteria": loteria_nombre,
                        "hora": hora_texto,
                        "hora_num": hora_num,
                        "numero": num_str,
                        "animal": nombre_animal,
                        "realizado": realizado
                    })

            historial[fecha_str] = resultados_fecha
            
            if es_hoy:
                with open("resultados.json", "w", encoding="utf-8") as f:
                    json.dump(resultados_fecha, f, ensure_ascii=False, indent=2)

        browser.close()

    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ejecutar_proceso_parley()
    print("Sincronización exclusiva de parley.la por tandas de 3 completada.")
