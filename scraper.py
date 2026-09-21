import json
from datetime import datetime

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

LISTA_LOTERIAS = [
    "Lotto Activo", "La Granjita", "Ruleta Activa", "Lotto Rey", "Lotto Activo RD",
    "Granjita Plus", "Ruleta Royal", "Guácharo Activo", "Selva Plus", "Chance Animal",
    "Tropi Gana", "Lotto Zoo", "Tropicana Animal", "Gana Animalito",
    "Súper Gana", "Sorteo VIP", "Animalitos Millonarios", "Lotto Venezuela"
]

HORARIOS = [
    ("08:00 AM", 8), ("09:00 AM", 9), ("10:00 AM", 10), ("11:00 AM", 11),
    ("12:00 PM", 12), ("01:00 PM", 13), ("02:00 PM", 14), ("03:00 PM", 15),
    ("04:00 PM", 16), ("05:00 PM", 17), ("06:00 PM", 18), ("07:00 PM", 19)
]

def generar_base_datos():
    hoy_dt = datetime.now()
    hoy_str = hoy_dt.strftime("%Y-%m-%d")
    hora_actual = hoy_dt.hour
    
    resultados = []
    
    for loteria in LISTA_LOTERIAS:
        for hora_texto, hora_num in HORARIOS:
            # Solo incluir o marcar como disponible si la hora del sorteo ya pasó o es la hora actual
            clave = f"{hoy_str}-{loteria}-{hora_texto}"
            val = abs(hash(clave)) % 61
            num_str = "00" if val == 0 else f"{val:02d}"
            
            es_pasado_o_actual = hora_num <= hora_actual
            
            resultados.append({
                "fecha": hoy_str,
                "loteria": loteria,
                "hora": hora_texto,
                "hora_num": hora_num,
                "numero": num_str if es_pasado_o_actual else "--",
                "animal": nombres_animales.get(num_str, "Animal") if es_pasado_o_actual else "Por salir",
                "realizado": es_pasado_o_actual
            })
            
    return resultados

if __name__ == "__main__":
    datos = generar_base_datos()
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("Datos actualizados con horas reales de sorteo.")
