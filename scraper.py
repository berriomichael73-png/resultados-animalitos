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

# Las 3 principales quedan fijas en parley.la; el resto utiliza su enlace dedicado individual
LOTERIAS_URLS = {
    "Lotto Activo": "https://m.parley.la/resultados/resultados-lotto-activo",
    "La Granjita": "https://m.parley.la/resultados/resultados-la-granjita",
    "Ruleta Activa": "https://m.parley.la/resultados/resultados-ruleta-activa",
    "Lotto Rey": "https://tuazar.com/loteria/animalitos/lotto-rey/resultados/",
    "Lotto Activo RD": "https://tuazar.com/loteria/animalitos/lotto-activo-rd/resultados/",
    "Granjita Plus": "https://tuazar.com/loteria/animalitos/la-granjita-plus/resultados/",
    "Ruleta Royal": "https://tuazar.com/loteria/animalitos/ruleta-royal/resultados/",
    "Guácharo Activo": "https://tuazar.com/loteria/animalitos/el-guacharo-activo/resultados/",
    "Selva Plus": "https://tuazar.com/loteria/animalitos/selva-plus/resultados/",
    "Chance Animal": "https://tuazar.com/loteria/animalitos/chance-animal/resultados/",
    "Tropi Gana": "https://tuazar.com/loteria/animalitos/tropigana/resultados/",
    "Lotto Zoo": "https://tuazar.com/loteria/animalitos/lotto-zoo/resultados/",
    "Tropicana Animal": "https://tuazar.com/loteria/animalitos/tropicana-animal/resultados/",
    "Gana Animalito": "https://tuazar.com/loteria/animalitos/gana-animalito/resultados/",
    "Súper Gana": "https://tuazar.com/loteria/animalitos/super-gana/resultados/",
    "Sorteo VIP": "https://tuazar.com/loteria/animalitos/sorteo-vip/resultados/",
    "Animalitos Millonarios": "https://tuazar.com/loteria/animalitos/animalitos-millonarios/resultados/",
    "Lotto Venezuela": "https://tuazar.com/loteria/animalitos/lotto-venezuela/resultados/"
}

HORARIOS = [
    ("08:00 AM", 8, r'08:00|\b8:00'),
    ("09:00 AM", 9, r'09:00|\b9:00'),
    ("10:00 AM", 10, r'10:00'),
    ("11:00 AM", 11, r'11:00'),
    ("12:00 PM", 12, r'12:00'),
    ("01:00 PM", 13, r'01:00|\b1:00'),
    ("02:00 PM", 14, r'02:00|\b2:00'),
    ("03:00 PM", 15, r'03:00|\b3:00'),
    ("04:00 PM", 16, r'04:00|\b4:00'),
    ("05:00 PM", 17, r'05:00|\b5:00'),
    ("06:00 PM", 18, r'06:00|\b6:00'),
    ("07:00 PM", 19, r'07:00|\b7:00')
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

                for hora_texto, hora_num, patron_hora in HORARIOS:
                    patron = re.compile(rf'({patron_hora}).*?(\d{{1,2}})\s+([A-Za-zÁéíóúñÁÉÍÓÚÑ]+)', re.IGNORECASE)
                    match = patron.search(texto_pagina)
                    
                    if match:
                        num_found = match.group(2).zfill(2)
                        clave = f"{loteria_nombre}-{hora_texto}"
                        mapa_resultados[clave] = num_found

            time.sleep(1)

        except Exception as e:
            print(f"Error procesando {loteria_nombre}: {e}")
            time.sleep(1)

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
        for hora_texto, hora_num, _ in HORARIOS:
            if hora_num <= hora_actual_ve:
                hora_objetivo_str = hora_texto
            else:
                break

        for hora_texto, hora_num, _ in HORARIOS:
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
    print("Sincronización por URL dedicada completada.")
