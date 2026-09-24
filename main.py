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

LOTERIAS_MAPPING = {
    "Lotto Activo": "https://loteriadehoy.com/images/lotto-activo.png",
    "La Granjita": "https://loteriadehoy.com/images/la-granjita.png",
    "Monje Millonario": "https://loteriadehoy.com/images/monje-millonario.png",
    "Guacharo Activo": "https://loteriadehoy.com/images/guacharo-activo.png",
    "El Guacharito": "https://loteriadehoy.com/images/el-guacharito-millonario.png",
    "Selva Plus": "https://loteriadehoy.com/images/selva-plus.png",
    "Centena Plus": "https://loteriadehoy.com/images/centena-plus.png",
    "Mega Animal": "https://loteriadehoy.com/images/mega-animal-40.png",
    "Lotto Activo RD": "https://loteriadehoy.com/images/lotto-activo-rd-int.png",
    "Centena Animalitos": "https://loteriadehoy.com/images/centena-animalitos.png",
    "Ruleta Activa": "https://loteriadehoy.com/images/ruleta-activa.png",
    "Chance": "https://loteriadehoy.com/images/chance-con-animalitos.png",
    "Ricachona": "https://loteriadehoy.com/images/la-ricachona.png"
}

HORARIOS_ESTANDAR = [
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
    "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM",
    "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM"
]

def obtener_fecha_venezuela():
    tz_ve = timezone(timedelta(hours=-4))
    return datetime.now(tz_ve).strftime("%Y-%m-%d")

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    hoy = obtener_fecha_venezuela()
    resultados_totales = []

    try:
        response = session.get("https://lotoven.com/animalitos/", headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos todas las tablas o bloques de resultados
            tablas = soup.find_all(['table', 'div', 'ul'])

            for loteria_nombre, logo in LOTERIAS_MAPPING.items():
                sorteos_obtenidos = {}

                for t in tablas:
                    txt = t.get_text(" ", strip=True)
                    if loteria_nombre.lower() in txt.lower() and len(txt) < 3000:
                        # Patron que busca combinaciones de Numero + Animal + Hora o Hora + Numero + Animal
                        matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*[-:\s]?\s*(\d{1,2})\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})', txt)
                        if not matches:
                            matches_inv = re.findall(r'(\d{1,2})\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})\s*[-:\s]?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', txt)
                            for num, animal, hora in matches_inv:
                                matches.append((hora, num, animal))

                        for hora, num, animal in matches:
                            h_clean = hora.strip().upper()
                            if "AM" not in h_clean and "PM" not in h_clean:
                                continue
                            
                            if h_clean not in sorteos_obtenidos:
                                sorteos_obtenidos[h_clean] = {
                                    "loteria": loteria_nombre,
                                    "logo_loteria": logo,
                                    "hora": h_clean,
                                    "numero": num.zfill(2),
                                    "animal": animal.strip().capitalize(),
                                    "realizado": True,
                                    "fecha": hoy
                                }

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

    except Exception as e:
        print(f"Error: {e}")

    return resultados_totales
