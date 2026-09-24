import json
import os
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from curl_cffi import requests

LOTERIAS_TUAZAR = {
    "Lotto Activo": {"tuazar": "lotto-activo", "logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"tuazar": "la-granjita", "logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje Millonario)": {"tuazar": "monje-millonario", "logo": "https://loteriadehoy.com/images/monje-millonario.png"},
    "Guacharo Activo": {"tuazar": "guacharo-activo", "logo": "https://loteriadehoy.com/images/guacharo-activo.png"},
    "El Guacharito Millonario": {"tuazar": "el-guacharito-millonario", "logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png"},
    "Selva Plus": {"tuazar": "selva-plus", "logo": "https://loteriadehoy.com/images/selva-plus.png"},
    "Centena Plus": {"tuazar": "centena-plus", "logo": "https://loteriadehoy.com/images/centena-plus.png"},
    "Lotto Activo Rd Int": {"tuazar": "lotto-activo-rd-int", "logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png"},
    "Mega Animal 40": {"tuazar": "mega-animal-40", "logo": "https://loteriadehoy.com/images/mega-animal-40.png"},
    "Centena Animalitos": {"tuazar": "centena-animalitos", "logo": "https://loteriadehoy.com/images/centena-animalitos.png"},
    "Chance Con Animalitos": {"tuazar": "chance-con-animalitos", "logo": "https://loteriadehoy.com/images/chance-con-animalitos.png"},
    "Cazaloton": {"tuazar": "cazaloton", "logo": "https://loteriadehoy.com/images/cazaloton.png"},
    "Ruleta Activa": {"tuazar": "ruleta-activa", "logo": "https://loteriadehoy.com/images/ruleta-activa.png"},
    "Granja Millonaria": {"tuazar": "granja-millonaria", "logo": "https://loteriadehoy.com/images/granja-millonaria.png"},
    "La-Ricachona": {"tuazar": "la-ricachona", "logo": "https://loteriadehoy.com/images/la-ricachona.png"},
    "Jungla Millonaria": {"tuazar": "jungla-millonaria", "logo": "https://loteriadehoy.com/images/jungla-millonaria.png"},
    "Loto Chaima": {"tuazar": "loto-chaima", "logo": "https://loteriadehoy.com/images/loto-chaima.png"},
    "Lotto Activo RDominicana": {"tuazar": "lotto-activo-rdominicana", "logo": "https://loteriadehoy.com/images/lotto-activo-rdominicana.png"}
}

HORARIOS_ORDENADOS = [
    ("08:00 AM", 8.0), ("09:00 AM", 9.0), ("10:00 AM", 10.0), ("11:00 AM", 11.0),
    ("12:00 PM", 12.0), ("01:00 PM", 13.0), ("02:00 PM", 14.0), ("03:00 PM", 15.0),
    ("04:00 PM", 16.0), ("05:00 PM", 17.0), ("06:00 PM", 18.0), ("07:00 PM", 19.0)
]

def obtener_fecha_venezuela():
    tz_ve = timezone(timedelta(hours=-4))
    return datetime.now(tz_ve).strftime("%Y-%m-%d")

def extraer_hora(texto):
    match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', texto)
    if match:
        h = match.group(1).strip().upper()
        if "AM" not in h and "PM" not in h:
            num = int(h.split(":")[0])
            h += " PM" if num in [12, 1, 2, 3, 4, 5, 6, 7] else " AM"
        return h
    return None

def extraer_animal_de_texto(texto):
    match = re.search(r'\b(\d{1,2})\b\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]+)', texto)
    if match:
        num = match.group(1).zfill(2)
        animal = match.group(2).strip()
        if len(animal) > 2 and animal.upper() not in ["AM", "PM", "POR", "SALIR"]:
            return num, animal.capitalize()
    return None, None

def extraer_tuazar_anti_bloqueo():
    # Inicialización del cliente con impersonación TLS de Chrome
    session = requests.Session()
    
    headers_base = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.105 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    resultados_totales = []

    for loteria_nombre, info in LOTERIAS_TUAZAR.items():
        sorteos_obtenidos = {}
        url_target = f"https://www.tuazar.com/triples/animalitos/{info['tuazar']}/"

        try:
            # Impersonación dinámica de huella TLS
            response = session.get(
                url_target,
                headers=headers_base,
                impersonate="chrome120",
                timeout=12
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                bloques = soup.find_all(['tr', 'div', 'li', 'td', 'article'])

                for b in bloques:
                    txt = b.get_text(" ", strip=True)
                    if len(txt) > 250:
                        continue

                    h = extraer_hora(txt)
                    if not h or h in sorteos_obtenidos:
                        continue

                    num, animal = None, None
                    img = b.find('img')

                    if img and img.get('src'):
                        src = img.get('src').lower()
                        if not ("logo" in src or "icon" in src or "banner" in src):
                            m = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src)
                            if m:
                                num = m.group(1).zfill(2)
                                animal = img.get('alt') or img.get('title') or "Animalito"

                    if not num:
                        num, animal = extraer_animal_de_texto(txt)

                    if num and animal:
                        sorteos_obtenidos[h] = {
                            "loteria": loteria_nombre,
                            "logo_loteria": info["logo"],
                            "hora": h,
                            "numero": num,
                            "animal": animal.strip().capitalize(),
                            "imagen": "",
                            "realizado": True
                        }

        except Exception as e:
            print(f"Error accediendo a {url_target}: {e}")

        # Normalización de los 12 horarios estándar
        for h_estandar, _ in HORARIOS_ORDENADOS:
            if h_estandar not in sorteos_obtenidos:
                sorteos_obtenidos[h_estandar] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": info["logo"],
                    "hora": h_estandar,
                    "numero": "--",
                    "animal": "Por salir",
                    "imagen": "",
                    "realizado": False
                }

        for h_estandar, _ in HORARIOS_ORDENADOS:
            if h_estandar in sorteos_obtenidos:
                resultados_totales.append(sorteos_obtenidos[h_estandar])

    return resultados_totales

def ejecutar():
    hoy = obtener_fecha_venezuela()

    historial = {}
    if os.path.exists("historial_resultados.json"):
        try:
            with open("historial_resultados.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    resultados_dia = extraer_tuazar_anti_bloqueo()

    for r in resultados_dia:
        r["fecha"] = hoy

    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_dia, f, ensure_ascii=False, indent=2)

    historial[hoy] = resultados_dia
    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    print("Proceso finalizado. Datos de TuAzar extraídos y guardados correctamente.")

if __name__ == "__main__":
    ejecutar()
