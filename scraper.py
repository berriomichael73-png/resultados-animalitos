import json
import os
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from curl_cffi import requests

LOTERIAS_CONFIG = {
    "Lotto Activo": {"slug": "lotto-activo", "logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"slug": "la-granjita", "logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje Millonario)": {"slug": "monje-millonario", "logo": "https://loteriadehoy.com/images/monje-millonario.png"},
    "Guacharo Activo": {"slug": "guacharo-activo", "logo": "https://loteriadehoy.com/images/guacharo-activo.png"},
    "El Guacharito Millonario": {"slug": "el-guacharito-millonario", "logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png"},
    "Selva Plus": {"slug": "selva-plus", "logo": "https://loteriadehoy.com/images/selva-plus.png"},
    "Centena Plus": {"slug": "centena-plus", "logo": "https://loteriadehoy.com/images/centena-plus.png"},
    "Lotto Activo Rd Int": {"slug": "lotto-activo-rd-int", "logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png"},
    "Mega Animal 40": {"slug": "mega-animal-40", "logo": "https://loteriadehoy.com/images/mega-animal-40.png"},
    "Centena Animalitos": {"slug": "centena-animalitos", "logo": "https://loteriadehoy.com/images/centena-animalitos.png"},
    "Chance Con Animalitos": {"slug": "chance-con-animalitos", "logo": "https://loteriadehoy.com/images/chance-con-animalitos.png"},
    "Cazaloton": {"slug": "cazaloton", "logo": "https://loteriadehoy.com/images/cazaloton.png"},
    "Ruleta Activa": {"slug": "ruleta-activa", "logo": "https://loteriadehoy.com/images/ruleta-activa.png"},
    "Granja Millonaria": {"slug": "granja-millonaria", "logo": "https://loteriadehoy.com/images/granja-millonaria.png"},
    "La-Ricachona": {"slug": "la-ricachona", "logo": "https://loteriadehoy.com/images/la-ricachona.png"},
    "Jungla Millonaria": {"slug": "jungla-millonaria", "logo": "https://loteriadehoy.com/images/jungla-millonaria.png"},
    "Loto Chaima": {"slug": "loto-chaima", "logo": "https://loteriadehoy.com/images/loto-chaima.png"},
    "Lotto Activo RDominicana": {"slug": "lotto-activo-rdominicana", "logo": "https://loteriadehoy.com/images/lotto-activo-rdominicana.png"}
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

def extraer_duo_dinamico():
    session = requests.Session()
    headers_base = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi Note 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    # Rescatar datos previos en caso de falla de conexion
    datos_previos = {}
    if os.path.exists("resultados.json"):
        try:
            with open("resultados.json", "r", encoding="utf-8") as f:
                lista_p = json.load(f)
                for item in lista_p:
                    clave = f"{item['loteria']}_{item['hora']}"
                    if item.get("realizado"):
                        datos_previos[clave] = item
        except Exception:
            datos_previos = {}

    resultados_totales = []

    for loteria_nombre, info in LOTERIAS_CONFIG.items():
        slug = info["slug"]
        logo = info["logo"]
        sorteos_obtenidos = {}

        # Múltiples URLs de respaldo alternando LoteríaDeHoy y Parley.la
        urls_prueba = [
            f"https://loteriadehoy.com/animalitos/{slug}",
            f"https://m.parley.la/resultados/resultados-{slug}",
            f"https://parley.la/resultados/{slug}"
        ]

        for url_target in urls_prueba:
            try:
                response = session.get(url_target, headers=headers_base, impersonate="chrome120", timeout=8)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    bloques = soup.find_all(['tr', 'div', 'li', 'article', 'td'])

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
                                "logo_loteria": logo,
                                "hora": h,
                                "numero": num,
                                "animal": animal.strip().capitalize(),
                                "imagen": "",
                                "realizado": True
                            }

                if sorteos_obtenidos:
                    break
            except Exception as e:
                print(f"Error consultando {url_target}: {e}")
                continue

        # Preservar o rellenar horarios
        for h_estandar, _ in HORARIOS_ORDENADOS:
            clave = f"{loteria_nombre}_{h_estandar}"
            if h_estandar not in sorteos_obtenidos and clave in datos_previos:
                sorteos_obtenidos[h_estandar] = datos_previos[clave]

            if h_estandar not in sorteos_obtenidos:
                sorteos_obtenidos[h_estandar] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": logo,
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

    resultados_dia = extraer_duo_dinamico()

    for r in resultados_dia:
        r["fecha"] = hoy

    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_dia, f, ensure_ascii=False, indent=2)

    historial[hoy] = resultados_dia
    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    print("Sincronización unificada de Parley.la + LoteríaDeHoy finalizada con éxito.")

if __name__ == "__main__":
    ejecutar()
