import json
import re
import time
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

LOTERIAS_URLS = {
    "Lotto Activo": "https://m.parley.la/resultados/resultados-lotto-activo",
    "La Granjita": "https://m.parley.la/resultados/resultados-la-granjita",
    "Ruleta Activa": "https://m.parley.la/resultados/resultados-ruleta-activa",
    "Lotto Rey": "https://agendadeportiva.com.ve/resultados-lotto-rey/",
    "Lotto Activo RD": "https://agendadeportiva.com.ve/resultados-lotto-activo-rd/",
    "Granjita Plus": "https://agendadeportiva.com.ve/resultados-la-granjita-plus/",
    "Ruleta Royal": "https://agendadeportiva.com.ve/resultados-ruleta-royal/",
    "Guácharo Activo": "https://agendadeportiva.com.ve/resultados-el-guacharo-activo/",
    "Selva Plus": "https://agendadeportiva.com.ve/resultados-selva-plus/",
    "Chance Animal": "https://agendadeportiva.com.ve/resultados-chance-animal/",
    "Tropi Gana": "https://agendadeportiva.com.ve/resultados-tropigana/",
    "Lotto Zoo": "https://agendadeportiva.com.ve/resultados-lotto-zoo/",
    "Tropicana Animal": "https://agendadeportiva.com.ve/resultados-tropicana-animal/",
    "Gana Animalito": "https://agendadeportiva.com.ve/resultados-gana-animalito/",
    "Súper Gana": "https://agendadeportiva.com.ve/resultados-super-gana/",
    "Sorteo VIP": "https://agendadeportiva.com.ve/resultados-sorteo-vip/",
    "Animalitos Millonarios": "https://agendadeportiva.com.ve/resultados-animalitos-millonarios/",
    "Lotto Venezuela": "https://agendadeportiva.com.ve/resultados-lotto-venezuela/"
}

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def extraer_resultados_por_loteria():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    mapa_resultados = {}
    session = requests.Session()

    for loteria_nombre, url in LOTERIAS_URLS.items():
        try:
            resp = session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                texto_pagina = soup.get_text(" ", strip=True)

                for hora_std, _ in HORARIOS:
                    hora_simple = hora_std.replace(":00", "").lower()
                    hora_full = hora_std.lower()
                    
                    # Expresión regular que busca la hora seguida de un número de animalito
                    patron = re.compile(rf'(?:{re.escape(hora_full)}|{re.escape(hora_simple)}).*?\b(\d{{1,2}})\b', re.IGNORECASE)
                    match = patron.search(texto_pagina)
                    
                    if match:
                        num_found = match.group(1).zfill(2)
                        clave = f"{loteria_nombre}-{hora_std}"
                        mapa_resultados[clave] = num_found

            time.sleep(0.5)

        except Exception as e:
            print(f"Error omitido en {loteria_nombre}: {e}")

    return mapa_resultados

def generar_base_datos():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour

    datos_reales = extraer_resultados_por_loteria()
    resultados = []

    for loteria in LOTERIAS_URLS.keys():
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
    print("Sincronización completada sin errores.")
