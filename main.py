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
    "Lotto Activo": {"logo": "https://loteriadehoy.com/images/lotto-activo.png"},
    "La Granjita": {"logo": "https://loteriadehoy.com/images/la-granjita.png"},
    "Lotto Activo 2 (Monje Millonario)": {"logo": "https://loteriadehoy.com/images/monje-millonario.png"},
    "Guacharo Activo": {"logo": "https://loteriadehoy.com/images/guacharo-activo.png"},
    "El Guacharito Millonario": {"logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png"},
    "Selva Plus": {"logo": "https://loteriadehoy.com/images/selva-plus.png"},
    "Centena Plus": {"logo": "https://loteriadehoy.com/images/centena-plus.png"},
    "Mega Animal 40": {"logo": "https://loteriadehoy.com/images/mega-animal-40.png"},
    "Lotto Activo RD Int": {"logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png"},
    "Centena Animalitos": {"logo": "https://loteriadehoy.com/images/centena-animalitos.png"},
    "Ruleta Activa": {"logo": "https://loteriadehoy.com/images/ruleta-activa.png"},
    "Chance Con Animalitos": {"logo": "https://loteriadehoy.com/images/chance-con-animalitos.png"},
    "La-Ricachona": {"logo": "https://loteriadehoy.com/images/la-ricachona.png"}
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    hoy = obtener_fecha_venezuela()
    resultados_totales = []

    try:
        # Peticion directa al agregador limpio LotoVen
        response = session.get("https://lotoven.com/animalitos/", headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            texto_completo = soup.get_text()

            # Estructura del portal: "* Resultados [Nombre Loteria]" seguido de "[Numero] [Animal] [Hora]"
            secciones = texto_completo.split("* Resultados")

            for sec in secciones[1:]:
                lineas = [l.strip() for l in sec.split("\n") if l.strip()]
                if not lineas:
                    continue

                nombre_loteria_raw = lineas[0].replace(".", "").strip()
                
                # Normalizar nombre de loteria
                loteria_oficial = None
                for k in LOTERIAS_MAPPING.keys():
                    if k.lower() in nombre_loteria_raw.lower():
                        loteria_oficial = k
                        break

                if not loteria_oficial:
                    loteria_oficial = nombre_loteria_raw

                logo = LOTERIAS_MAPPING.get(loteria_oficial, {}).get("logo", "https://loteriadehoy.com/images/lotto-activo.png")
                sorteos_obtenidos = {}

                # Extraer entradas del tipo "28 Zamuro 08:00 AM"
                patron = re.compile(r'(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóúÑñ\s]+?)\s+(\d{1,2}:\d{2}\s*(?:AM|PM))', re.IGNORECASE)
                matches = patron.findall(sec)

                for num, animal, hora in matches:
                    hora_clean = hora.strip().upper()
                    sorteos_obtenidos[hora_clean] = {
                        "loteria": loteria_oficial,
                        "logo_loteria": logo,
                        "hora": hora_clean,
                        "numero": num.zfill(2),
                        "animal": animal.strip().capitalize(),
                        "realizado": True,
                        "fecha": hoy
                    }

                # Rellenar con 'Por salir' los horarios estándar sin sorteo realizado
                for h_estandar in HORARIOS_ESTANDAR:
                    if h_estandar not in sorteos_obtenidos:
                        sorteos_obtenidos[h_estandar] = {
                            "loteria": loteria_oficial,
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
        print(f"Error extrayendo datos: {e}")

    return resultados_totales
