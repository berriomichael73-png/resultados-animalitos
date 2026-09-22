import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

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

# Mapeo de loterías a las URLs directas de Parley.la
LOTERIAS_PARLEY = {
    "Lotto Activo": "https://m.parley.la/resultados/resultados-lotto-activo",
    "La Granjita": "https://m.parley.la/resultados/resultados-la-granjita",
    "Ruleta Activa": "https://m.parley.la/resultados/resultados-ruleta-activa",
    "Lotto Rey": "https://m.parley.la/resultados/resultados-lotto-rey",
    "Lotto Activo RD": "https://m.parley.la/resultados/resultados-lotto-activo-rd",
    "Granjita Plus": "https://m.parley.la/resultados/resultados-la-granjita-plus",
    "Ruleta Royal": "https://m.parley.la/resultados/resultados-ruleta-royal",
    "Guácharo Activo": "https://m.parley.la/resultados/resultados-el-guacharo-activo",
    "Selva Plus": "https://m.parley.la/resultados/resultados-selva-plus",
    "Chance Animal": "https://m.parley.la/resultados/resultados-chance-animal",
    "Tropi Gana": "https://m.parley.la/resultados/resultados-tropigana",
    "Lotto Zoo": "https://m.parley.la/resultados/resultados-lotto-zoo",
    "Tropicana Animal": "https://m.parley.la/resultados/resultados-tropicana-animal",
    "Gana Animalito": "https://m.parley.la/resultados/resultados-gana-animalito",
    "Súper Gana": "https://m.parley.la/resultados/resultados-super-gana",
    "Sorteo VIP": "https://m.parley.la/resultados/resultados-sorteo-vip",
    "Animalitos Millonarios": "https://m.parley.la/resultados/resultados-animalitos-millonarios",
    "Lotto Venezuela": "https://m.parley.la/resultados/resultados-lotto-venezuela"
}

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def extraer_resultados_parley():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    mapa_resultados = {}

    for loteria_nombre, url in LOTERIAS_PARLEY.items():
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                texto_pagina = soup.get_text()

                # Busca patrones de texto oficiales como "08:00 am. Fecha: ... 18 BURRO" o "09:00 am ... 10 TIGRE"
                for hora_texto, _ in HORARIOS:
                    hora_clean = hora_texto.lower()
                    # Expresión para capturar el número que sigue a la hora
                    patron = re.compile(rf'{hora_clean}.*?(\d{{1,2}})\s+([A-Za-zÁéíóúñÁÉÍÓÚÑ]+)', re.IGNORECASE | re.DOTALL)
                    match = patron.search(texto_pagina)
                    
                    if match:
                        num_found = match.group(1).zfill(2)
                        clave = f"{loteria_nombre}-{hora_texto}"
                        mapa_resultados[clave] = num_found
        except Exception as e:
            print(f"Error procesando {loteria_nombre} en Parley: {e}")

    return mapa_resultados

def generar_base_datos():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour

    datos_reales = extraer_resultados_parley()
    resultados = []

    for loteria in LOTERIAS_PARLEY.keys():
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

            resultados.append({
                "fecha": hoy_str,
                "loteria": loteria,
                "hora": hora_texto,
                "hora_num": hora_num,
                "numero": num_str,
                "animal": nombre_animal,
                "realizado": realizado,
                "es_ultimo_en_vivo": (hora_texto == hora_objetivo_str)
            })

    return resultados

if __name__ == "__main__":
    datos = generar_base_datos()
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("Sincronización con Parley.la finalizada correctamente.")
