import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import cloudscraper

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

def escanear_directo_http():
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'desktop': False
        }
    )

    resultados_totales = []

    for loteria_nombre, info in LOTERIAS_OFICIALES.items():
        sorteos_obtenidos = {}

        urls = [
            f"https://www.tuazar.com/triples/animalitos/{info['tuazar']}/",
            f"https://loteriadehoy.com/animalitos/{info['slugs'][0]}"
        ]

        for url in urls:
            try:
                resp = scraper.get(url, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    bloques = soup.find_all(['tr', 'div', 'li', 'td'])

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
                            if not ("logo" in src or "icon" in src):
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

                if sorteos_obtenidos:
                    break
            except Exception as e:
                print(f"Error consultando {url}: {e}")

        # Rellenar horas pendientes
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

    resultados_dia = escanear_directo_http()

    for r in resultados_dia:
        r["fecha"] = hoy

    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_dia, f, ensure_ascii=False, indent=2)

    historial[hoy] = resultados_dia
    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    print("Actualización completada vía HTTP directo.")

if __name__ == "__main__":
    ejecutar()
