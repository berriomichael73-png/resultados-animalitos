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

# Slugs asignados para mapeo multicanal
LOTERIAS_CONFIG = {
    "Lotto Activo": ["lotto-activo", "lottoactivo"],
    "La Granjita": ["la-granjita", "lagranjita"],
    "Ruleta Activa": ["ruleta-activa", "ruletaactiva"],
    "Lotto Rey": ["lotto-rey", "lottorey"],
    "Lotto Activo RD": ["lotto-activo-rd", "lottoactivord"],
    "Granjita Plus": ["la-granjita-plus", "granjitaplus"],
    "Ruleta Royal": ["ruleta-royal", "ruletaroyal"],
    "Guácharo Activo": ["el-guacharo-activo", "guacharo-activo"],
    "Selva Plus": ["selva-plus", "selvaplus"],
    "Chance Animal": ["chance-animal", "chanceanimal"],
    "Tropi Gana": ["tropigana", "tropi-gana"],
    "Lotto Zoo": ["lotto-zoo", "lottozoo"],
    "Tropicana Animal": ["tropicana-animal", "tropicana"],
    "Gana Animalito": ["gana-animalito", "ganaanimalito"],
    "Súper Gana": ["super-gana", "supergana"],
    "Sorteo VIP": ["sorteo-vip", "sorteovip"],
    "Animalitos Millonarios": ["animalitos-millonarios", "millonarios"],
    "Lotto Venezuela": ["lotto-venezuela", "lottovenezuela"]
}

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def obtener_urls_loteria(loteria_nombre):
    slugs = LOTERIAS_CONFIG[loteria_nombre]
    
    # Generar lista de fuentes secundarias y principales por lotería
    urls = [
        f"https://m.parley.la/resultados/resultados-{slugs[0]}",
        f"https://agendadeportiva.com.ve/resultados-{slugs[0]}/",
        f"https://tuazar.com/loteria/animalitos/{slugs[0]}/resultados/"
    ]
    return urls

def buscar_estricto_en_html(soup, hora_std):
    hora_base = hora_std[:2]
    hora_alt = str(int(hora_base))
    periodo = hora_std[-2:].lower()

    # Buscar contenedores específicos (filas de tabla, tarjetas o elementos li)
    elementos = soup.find_all(["tr", "div", "li", "p"])

    for el in elementos:
        texto_bloque = el.get_text(" ", strip=True).lower()

        # Verificar si este bloque específico contiene la hora
        if (f"{hora_base}:00" in texto_bloque or f"{hora_alt}:00" in texto_bloque) and (periodo in texto_bloque or "am" in texto_bloque or "pm" in texto_bloque):
            # Buscar coincidencia estricta de Animal + Número en el mismo contenedor
            for num_code, nombre_anim in nombres_animales.items():
                nombre_clean = nombre_anim.lower()
                num_clean = num_code.zfill(2)

                if nombre_clean in texto_bloque:
                    # Validar que el número también aparezca en el bloque o corresponda exactamente al animal
                    if num_clean in texto_bloque or str(int(num_clean)) in texto_bloque:
                        return num_clean

    return None

def busqueda_masiva_estricta():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache"
    }

    mapa_resultados = {}
    session = requests.Session()

    for loteria_nombre in LOTERIAS_CONFIG.keys():
        urls = obtener_urls_loteria(loteria_nombre)

        for hora_std, _ in HORARIOS:
            clave = f"{loteria_nombre}-{hora_std}"
            
            # Recorrer fuentes masivas hasta encontrar la coincidencia estricta de esa hora
            for url in urls:
                if clave in mapa_resultados:
                    break

                try:
                    url_time = f"{url}?t={int(time.time())}"
                    resp = session.get(url_time, headers=headers, timeout=6)

                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        num_encontrado = buscar_estricto_en_html(soup, hora_std)

                        if num_encontrado:
                            mapa_resultados[clave] = num_encontrado

                except Exception:
                    continue

            time.sleep(0.1)

    return mapa_resultados

def generar_base_datos():
    tz_ve = timezone(timedelta(hours=-4))
    hoy_dt = datetime.now(tz_ve)
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual_ve = hoy_dt.hour

    datos_reales = busqueda_masiva_estricta()
    resultados = []

    for loteria in LOTERIAS_CONFIG.keys():
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
    print("Sincronización masiva y estricta completada con éxito.")
