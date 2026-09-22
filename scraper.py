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

# Mapa de URLs directas corregidas para LotoVen
LOTERIAS_URLS = {
    "Lotto Activo": "https://lotoven.com/animalito/lottoactivo/resultados/",
    "La Granjita": "https://lotoven.com/animalito/lagranjita/resultados/",
    "Ruleta Activa": "https://lotoven.com/animalito/ruletaactiva/resultados/",
    "Lotto Rey": "https://lotoven.com/animalito/lottorey/resultados/",
    "Lotto Activo RD": "https://lotoven.com/animalito/lottoactivordint/resultados/",
    "Granjita Plus": "https://lotoven.com/animalito/granjitaplus/resultados/",
    "Ruleta Royal": "https://lotoven.com/animalito/ruletaroyal/resultados/",
    "Guácharo Activo": "https://lotoven.com/animalito/guacharoactivo/resultados/",
    "Selva Plus": "https://lotoven.com/animalito/selvaplus/resultados/",
    "Chance Animal": "https://lotoven.com/animalito/chanceanimal/resultados/",
    "Tropi Gana": "https://lotoven.com/animalito/tropigana/resultados/",
    "Lotto Zoo": "https://lotoven.com/animalito/lottozoo/resultados/",
    "Tropicana Animal": "https://lotoven.com/animalito/tropicanaanimal/resultados/",
    "Gana Animalito": "https://lotoven.com/animalito/ganaanimalito/resultados/",
    "Súper Gana": "https://lotoven.com/animalito/supergana/resultados/",
    "Sorteo VIP": "https://lotoven.com/animalito/sorteovip/resultados/",
    "Animalitos Millonarios": "https://lotoven.com/animalito/animalitosmillonarios/resultados/",
    "Lotto Venezuela": "https://lotoven.com/animalito/lottovenezuela/resultados/"
}

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def obtener_resultados_flexibles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    mapa_resultados = {}

    for nombre_loteria, url in LOTERIAS_URLS.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                texto_limpio = soup.get_text()

                # Busca patrones del tipo "30 Caiman ... 08:00 AM" o "12 Caballo ... 10:00 AM"
                patron = re.compile(r'(\d{1,2})\s+([A-Za-zÁéíóúñÁÉÍÓÚÑ]+).*?((?:0[1-9]|1[0-2]):00\s+(?:AM|PM))', re.DOTALL)
                coincidencias = patron.findall(texto_limpio)

                for match in coincidencias:
                    num_bruto, animal_nom, hora_str = match
                    num_str = num_bruto.zfill(2)
                    clave = f"{nombre_loteria}-{hora_str}"
                    if clave not in mapa_resultados:
                        mapa_resultados[clave] = num_str
        except Exception as e:
            print(f"Error parseando {nombre_loteria}: {e}")

    return mapa_resultados

def generar_base_datos():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour

    datos_reales = obtener_resultados_flexibles()
    resultados = []

    for loteria in LOTERIAS_URLS.keys():
        # Calcular la hora más reciente según la hora venezolana
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
                "numero": num_str if es_pasado_o_actual else "--",
                "animal": nombre_animal if es_pasado_o_actual else "Por salir",
                "realizado": realizado,
                "es_ultimo_en_vivo": (hora_texto == hora_objetivo_str)
            })

    return resultados

if __name__ == "__main__":
    datos = generar_base_datos()
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("Base de datos procesada exitosamente.")
