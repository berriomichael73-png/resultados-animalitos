from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from curl_cffi import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mapeo directo y centralizado en loteriadehoy.com
LOTERIAS_CONFIG = {
    "Lotto Activo": {"slug": "lotto-activo", "logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"slug": "la-granjita", "logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje)": {"slug": "monje-millonario", "logo": "https://loteriadehoy.com/images/monje-millonario.png"},
    "Guacharo Activo": {"slug": "guacharo-activo", "logo": "https://loteriadehoy.com/images/guacharo-activo.png"},
    "El Guacharito": {"slug": "el-guacharito-millonario", "logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png"},
    "Selva Plus": {"slug": "selva-plus", "logo": "https://loteriadehoy.com/images/selva-plus.png"},
    "Centena Plus": {"slug": "centena-plus", "logo": "https://loteriadehoy.com/images/centena-plus.png"},
    "Lotto Activo RD": {"slug": "lotto-activo-rd-int", "logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png"},
    "Mega Animal 40": {"slug": "mega-animal-40", "logo": "https://loteriadehoy.com/images/mega-animal-40.png"},
    "Centena Animalitos": {"slug": "centena-animalitos", "logo": "https://loteriadehoy.com/images/centena-animalitos.png"},
    "Chance Animalitos": {"slug": "chance-con-animalitos", "logo": "https://loteriadehoy.com/images/chance-con-animalitos.png"},
    "Ruleta Activa": {"slug": "ruleta-activa", "logo": "https://loteriadehoy.com/images/ruleta-activa.png"},
    "Granja Millonaria": {"slug": "granja-millonaria", "logo": "https://loteriadehoy.com/images/granja-millonaria.png"},
    "La Ricachona": {"slug": "la-ricachona", "logo": "https://loteriadehoy.com/images/la-ricachona.png"}
}

HORARIOS_ESTANDAR = [
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
    "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM",
    "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM"
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
            h += " PM" if num in [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] else " AM"
        return h
    return None

def extraer_animal_de_texto(texto):
    match = re.search(r'\b(\d{1,2})\b\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})', texto)
    if match:
        num = match.group(1).zfill(2)
        animal = match.group(2).strip()
        palabras_ignorar = ["AM", "PM", "POR", "SALIR", "RESULTADO", "RESULTADOS", "LOTERIA", "SORTEO"]
        if animal.upper() not in palabras_ignorar:
            return num, animal.capitalize()
    return None, None

def convertir_hora_a_minutos(hora_str):
    try:
        parts = hora_str.replace(" ", "").upper()
        es_pm = "PM" in parts
        es_am = "AM" in parts
        clean_time = parts.replace("AM", "").replace("PM", "")
        h, m = map(int, clean_time.split(":"))
        if es_pm and h < 12:
            h += 12
        if es_am and h == 12:
            h = 0
        return h * 60 + m
    except Exception:
        return 9999

@app.get("/resultados")
def obtener_resultados():
    session = requests.Session()
    headers_base = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    hoy = obtener_fecha_venezuela()
    resultados_totales = []

    for loteria_nombre, info in LOTERIAS_CONFIG.items():
        slug = info["slug"]
        logo = info["logo"]
        sorteos_obtenidos = {}

        url_target = f"https://loteriadehoy.com/animalitos/{slug}"

        try:
            response = session.get(url_target, headers=headers_base, impersonate="chrome120", timeout=3)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                bloques = soup.find_all(['tr', 'td', 'div', 'li'])

                for b in bloques:
                    txt = b.get_text(" ", strip=True)
                    if len(txt) > 200:
                        continue

                    h = extraer_hora(txt)
                    if not h or h in sorteos_obtenidos:
                        continue

                    num, animal = None, None
                    img = b.find('img')

                    if img and img.get('src'):
                        src = img.get('src').lower()
                        alt_txt = img.get('alt', '') or img.get('title', '')
                        m = re.search(r'/(?:0?(\d{1,2}))\.(?:png|jpg|jpeg|webp)', src)
                        if m:
                            num = m.group(1).zfill(2)
                            animal = alt_txt if len(alt_txt) > 2 else None

                    if not num or not animal:
                        num_txt, animal_txt = extraer_animal_de_texto(txt)
                        num = num or num_txt
                        animal = animal or animal_txt

                    if num and animal:
                        sorteos_obtenidos[h] = {
                            "loteria": loteria_nombre,
                            "logo_loteria": logo,
                            "hora": h,
                            "numero": num,
                            "animal": animal.strip().capitalize(),
                            "realizado": True,
                            "fecha": hoy
                        }
        except Exception:
            pass

        # Completar los horarios que falten como 'Por salir'
        for h_estandar in HORARIOS_ESTANDAR:
            if h_estandar not in sorteos_obtenidos:
                sorteos_obtenidos[h_estandar] = {
                    "loteria": loteria_nombre,
                    "logo_loteria": logo,
                    "hora": h_estandar,
                    "numero": "--",
                    "animal": "Por salir",
                    "realizado": False,
                    "fecha": hoy
                }

        sorteos_ordenados = sorted(
            sorteos_obtenidos.values(), 
            key=lambda x: convertir_hora_a_minutos(x["hora"])
        )

        resultados_totales.extend(sorteos_ordenados)

    return resultados_totales
