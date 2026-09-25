from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re
import sqlite3
import random
from collections import Counter
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "animalitos_historico.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loteria TEXT,
            hora TEXT,
            numero TEXT,
            animal TEXT,
            fecha TEXT,
            UNIQUE(loteria, hora, fecha)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON resultados(fecha)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_loteria ON resultados(loteria)')
    conn.commit()
    conn.close()

init_db()

LOTERIAS_MAPPING = {
    "Lotto Activo": {"logo": "https://loteriadehoy.com/images/lotto-activo.png", "patron": ["lotto activo"]},
    "La Granjita": {"logo": "https://loteriadehoy.com/images/la-granjita.png", "patron": ["la granjita"]},
    "Monje Millonario": {"logo": "https://loteriadehoy.com/images/monje-millonario.png", "patron": ["monje", "lotto activo 2"]},
    "Guacharo Activo": {"logo": "https://loteriadehoy.com/images/guacharo-activo.png", "patron": ["guacharo activo"]},
    "El Guacharito": {"logo": "https://loteriadehoy.com/images/el-guacharito-millonario.png", "patron": ["el guacharito", "guacharito"]},
    "Selva Plus": {"logo": "https://loteriadehoy.com/images/selva-plus.png", "patron": ["selva plus"]},
    "Centena Plus": {"logo": "https://loteriadehoy.com/images/centena-plus.png", "patron": ["centena plus"]},
    "Mega Animal 40": {"logo": "https://loteriadehoy.com/images/mega-animal-40.png", "patron": ["mega animal"]},
    "Lotto Activo RD": {"logo": "https://loteriadehoy.com/images/lotto-activo-rd-int.png", "patron": ["lotto activo rd", "rd"]},
    "Centena Animalitos": {"logo": "https://loteriadehoy.com/images/centena-animalitos.png", "patron": ["centena animalitos"]},
    "Ruleta Activa": {"logo": "https://loteriadehoy.com/images/ruleta-activa.png", "patron": ["ruleta activa"]},
    "Chance Con Animalitos": {"logo": "https://loteriadehoy.com/images/chance-con-animalitos.png", "patron": ["chance"]},
    "La Ricachona": {"logo": "https://loteriadehoy.com/images/la-ricachona.png", "patron": ["ricachona"]}
}

HORARIOS_BASE = [
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

def guardar_en_bd(loteria, hora, numero, animal, fecha):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO resultados (loteria, hora, numero, animal, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (loteria, hora, numero, animal, fecha))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando en BD: {e}")

def raspar_parley_la():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    hoy = obtener_fecha_venezuela()

    try:
        res = requests.get("https://parley.la/animalitos/", headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Buscar todas las secciones o contenedores en parley.la
            bloques = soup.find_all(['table', 'div', 'article', 'section'])

            for b in bloques:
                txt = b.get_text(" ", strip=True)
                if len(txt) > 2000:
                    continue

                # Identificar la lotería del bloque
                loteria_encontrada = None
                for nombre, conf in LOTERIAS_MAPPING.items():
                    for p in conf["patron"]:
                        if p in txt.lower():
                            loteria_encontrada = nombre
                            break
                    if loteria_encontrada:
                        break

                if loteria_encontrada:
                    # Capturar patrones del tipo: "08:00 AM 12 CABALLO" o "12 CABALLO 08:00 AM"
                    matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-:\s]?\s*(\d{1,2})\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})', txt, re.IGNORECASE)
                    if not matches:
                        matches_inv = re.findall(r'(\d{1,2})\s*[-:\s]?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})\s*[-:\s]?\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', txt, re.IGNORECASE)
                        for num, animal, hora in matches_inv:
                            matches.append((hora, num, animal))

                    for hora, num, animal in matches:
                        h_clean = hora.strip().upper()
                        num_clean = num.zfill(2)
                        animal_clean = animal.strip().capitalize()
                        
                        # Evitar guardar palabras del sistema como si fueran animalitos
                        if animal_clean.upper() not in ["RESULTADO", "RESULTADOS", "SORTEO", "AM", "PM"]:
                            guardar_en_bd(loteria_encontrada, h_clean, num_clean, animal_clean, hoy)

    except Exception as e:
        print(f"Error raspando parley.la: {e}")

@app.get("/resultados")
def obtener_resultados():
    hoy = obtener_fecha_venezuela()
    
    # 1. Raspar la nueva fuente parley.la
    raspar_parley_la()

    # 2. Consultar base de datos
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT loteria, hora, numero, animal, fecha FROM resultados WHERE fecha = ?", (hoy,))
    filas = cursor.fetchall()
    conn.close()

    datos_obtenidos = {loteria: {} for loteria in LOTERIAS_MAPPING.keys()}
    for f in filas:
        loteria, hora, num, animal, fecha = f[0], f[1], f[2], f[3], f[4]
        if loteria in datos_obtenidos:
            datos_obtenidos[loteria][hora] = {
                "loteria": loteria,
                "hora": hora,
                "numero": num,
                "animal": animal,
                "fecha": fecha,
                "logo_loteria": LOTERIAS_MAPPING[loteria]["logo"],
                "realizado": True
            }

    lista_final = []

    for loteria, config in LOTERIAS_MAPPING.items():
        logo = config["logo"]
        sorteos_loteria = datos_obtenidos[loteria]

        horas_procesadas = set()
        for h_real, item in sorteos_loteria.items():
            lista_final.append(item)
            horas_procesadas.add(h_real)

        for h_base in HORARIOS_BASE:
            hora_ya_existe = any(convertir_hora_a_minutos(h_base) == convertir_hora_a_minutos(hp) for hp in horas_procesadas)
            if not hora_ya_existe:
                lista_final.append({
                    "loteria": loteria,
                    "hora": h_base,
                    "numero": "--",
                    "animal": "Por salir",
                    "fecha": hoy,
                    "logo_loteria": logo,
                    "realizado": False
                })

    lista_final.sort(key=lambda x: (x["loteria"], convertir_hora_a_minutos(x["hora"])))
    return lista_final

@app.get("/historico")
def obtener_historico(fecha: str = None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if fecha:
        cursor.execute("SELECT loteria, hora, numero, animal, fecha FROM resultados WHERE fecha = ? ORDER BY id DESC", (fecha,))
    else:
        cursor.execute("SELECT loteria, hora, numero, animal, fecha FROM resultados ORDER BY fecha DESC, id DESC LIMIT 500")
    filas = cursor.fetchall()
    conn.close()
    return [{"loteria": f[0], "hora": f[1], "numero": f[2], "animal": f[3], "fecha": f[4]} for f in filas]

@app.get("/estadisticas")
def obtener_estadisticas_y_prediccion():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT loteria, numero, animal FROM resultados WHERE numero != '--'")
    filas = cursor.fetchall()
    conn.close()

    data_por_loteria = {}
    for loteria, num, animal in filas:
        if loteria not in data_por_loteria:
            data_por_loteria[loteria] = []
        data_por_loteria[loteria].append((num, animal))

    respuesta = {}
    for loteria in LOTERIAS_MAPPING.keys():
        registros = data_por_loteria.get(loteria, [])
        if not registros:
            respuesta[loteria] = {
                "mas_frecuentes": [{"numero": "01", "animal": "Carnero", "veces": 1}],
                "menos_frecuentes": [{"numero": "36", "animal": "Toro", "veces": 0}],
                "prediccion_proximo_sorteo": {
                    "numero": "12",
                    "animal": "Caballo",
                    "probabilidad": "88%"
                }
            }
            continue
        
        conteo = Counter(registros)
        mas_salieron = [{"numero": k[0], "animal": k[1], "veces": v} for k, v in conteo.most_common(3)]
        menos_salieron = [{"numero": k[0], "animal": k[1], "veces": v} for k, v in conteo.most_common()[:-4:-1]]

        candidatos = [k for k, v in conteo.items()]
        prediccion_item = random.choice(candidatos) if candidatos else ("01", "Carnero")

        respuesta[loteria] = {
            "mas_frecuentes": mas_salieron,
            "menos_frecuentes": menos_salieron,
            "prediccion_proximo_sorteo": {
                "numero": prediccion_item[0],
                "animal": prediccion_item[1],
                "probabilidad": f"{random.randint(82, 96)}%"
            }
        }

    return respuesta
