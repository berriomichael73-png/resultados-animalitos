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

LISTA_LOTERIAS = [
    "Lotto Activo", "La Granjita", "Ruleta Activa", "Lotto Rey", "Lotto Activo RD",
    "Granjita Plus", "Ruleta Royal", "Guácharo Activo", "Selva Plus", "Chance Animal",
    "Tropi Gana", "Lotto Zoo", "Tropicana Animal", "Gana Animalito",
    "Súper Gana", "Sorteo VIP", "Animalitos Millonarios", "Lotto Venezuela"
]

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def procesar_fila_especifica(fila_html):
    imgs = fila_html.find_all("img")
    for img in imgs:
        src = img.get("src", "").lower()
        alt = img.get("alt", "").lower()
        title = img.get("title", "").lower()
        
        for num_code, anim_nombre in nombres_animales.items():
            nombre_clean = anim_nombre.lower()
            if nombre_clean in alt or nombre_clean in title or nombre_clean in src:
                return num_code.zfill(2)
        
        match_src = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src)
        if match_src:
            num_cand = match_src.group(1).zfill(2)
            if num_cand in nombres_animales:
                return num_cand

    txt_fila = fila_html.get_text(" ", strip=True)
    for num_code, anim_nombre in nombres_animales.items():
        if anim_nombre.lower() in txt_fila.lower():
            return num_code.zfill(2)

    return None

def extraer_con_playwright():
    mapa_resultados = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto("https://loteriadehoy.com/animalitos/resultados/", timeout=40000)
            page.wait_for_timeout(5000)
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            tarjetas = soup.find_all(["div", "section", "article", "table"], class_=re.compile(r'card|block|tabla|resultado|loteria', re.I))
            if not tarjetas:
                tarjetas = [soup]

            for tarjeta in tarjetas:
                txt_tarjeta = tarjeta.get_text(" ", strip=True)
                
                loteria_detectada = None
                for lot in LISTA_LOTERIAS:
                    if lot.lower() in txt_tarjeta[:120].lower():
                        loteria_detectada = lot
                        break
                
                if loteria_detectada:
                    filas = tarjeta.find_all(["tr", "li", "div"], class_=re.compile(r'item|row|fila|sorteo|hora', re.I))
                    if not filas:
                        filas = tarjeta.find_all(["tr", "li"])

                    for f in filas:
                        txt_f = f.get_text(" ", strip=True)
                        for hora_std, _ in HORARIOS:
                            clave = f"{loteria_detectada}-{hora_std}"
                            if clave in mapa_resultados:
                                continue
                            
                            hora_num = hora_std[:2]
                            hora_alt = str(int(hora_num))
                            
                            if f"{hora_num}:00" in txt_f or f"{hora_alt}:00" in txt_f:
                                res_num = procesar_fila_especifica(f)
                                if res_num:
                                    mapa_resultados[clave] = res_num

        except Exception as e:
            print(f"Error procesando extracción: {e}")
        finally:
            browser.close()
            
    return mapa_resultados

def actualizar_historial_y_diario():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour

    datos_reales = extraer_con_playwright()
    resultados_hoy = []

    for loteria in LISTA_LOTERIAS:
        hora_objetivo_str = "08:00 AM"
        for hora_texto, hora_num in HORARIOS:
            if hora_num <= hora_actual_ve:
                hora_objetivo_str = hora_texto
            else:
                break

        for hora_texto, hora_num in HORARIOS:
            es_pasado_o_actual = hora_num <= hora_actual_ve
            clave = f"{loteria}-{hora_texto}"

            if clave in datos_reales and es_pasado_o_actual:
                num_str = datos_reales[clave]
                nombre_animal = nombres_animales.get(num_str, "Animal")
                realizado = True
            else:
                num_str = "--"
                nombre_animal = "Por salir"
                realizado = False

            resultados_hoy.append({
                "fecha": hoy_str,
                "loteria": loteria,
                "hora": hora_texto,
                "hora_num": hora_num,
                "numero": num_str,
                "animal": nombre_animal,
                "realizado": realizado,
                "es_ultimo_en_vivo": (hora_texto == hora_objetivo_str)
            })

    # Guardar resultados del día
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_hoy, f, ensure_ascii=False, indent=2)

    # Cargar y actualizar historial acumulativo
    historial = {}
    if os.path.exists("historial_resultados.json"):
        try:
            with open("historial_resultados.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    # Agregar o reemplazar la fecha de hoy en el historial
    historial[hoy_str] = resultados_hoy

    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    actualizar_historial_y_diario()
    print("Sincronización diaria e historial acumulativo guardados correctamente.")
