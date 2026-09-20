import json
from datetime import datetime

nombres_animales = {
    "00": "Delfín", "0": "Delfín",
    "1": "Carnero", "01": "Carnero",
    "2": "Toro", "02": "Toro",
    "3": "Ciempiés", "03": "Ciempiés",
    "4": "Escorpión", "04": "Escorpión",
    "5": "León", "05": "León",
    "6": "Rana", "06": "Rana",
    "7": "Perico", "07": "Perico",
    "8": "Ratón", "08": "Ratón",
    "9": "Águila", "09": "Águila",
    "10": "Tigre", "11": "Gato", "12": "Caballo", "13": "Mono", "14": "Paloma",
    "15": "Zorro", "16": "Oso", "17": "Pavo", "18": "Burro", "19": "Chivo",
    "20": "Cochino", "21": "Gallo", "22": "Camello", "23": "Cebra", "24": "Iguana",
    "25": "Gallina", "26": "Vaca", "27": "Perro", "28": "Zamuro", "29": "Elefante",
    "30": "Caimán", "31": "Lapa", "32": "Ardilla", "33": "Pescado", "34": "Venado",
    "35": "Jirafa", "36": "Culebra", "37": "Abeja", "38": "Erizo", "39": "Flamenco",
    "40": "Foca", "41": "Canguro", "42": "Perezoso", "43": "Zorrillo", "44": "Nutria",
    "45": "Tejón", "46": "Mamut", "47": "Dodo", "48": "Pavo Real", "49": "Búho",
    "50": "Murciélago", "51": "Medusa", "52": "Pulpo", "53": "Langosta", "54": "Cangrejo",
    "55": "Ostra", "56": "Mariposa", "57": "Hormiga", "58": "Mariquita", "59": "Grillo",
    "60": "Araña"
}

def generar_resultados():
    ahora = datetime.now()
    hora_actual = ahora.hour
    
    if hora_actual < 8:
        hora_sorteo = "08:00 AM"
    elif hora_actual > 19:
        hora_sorteo = "07:00 PM"
    else:
        ampm = "PM" if hora_actual >= 12 else "AM"
        h12 = hora_actual % 12
        h12 = 12 if h12 == 0 else h12
        hora_sorteo = f"{h12:02d}:00 {ampm}"

    loterias = [
        {"nombre": "Lotto Activo", "max": 36},
        {"nombre": "La Granjita", "max": 60},
        {"nombre": "Ruleta Activa", "max": 36},
        {"nombre": "Lotto Rey", "max": 36},
        {"nombre": "Lotto Activo RD", "max": 36},
        {"nombre": "Granjita Plus", "max": 60},
        {"nombre": "Ruleta Royal", "max": 36},
        {"nombre": "Guácharo Activo", "max": 36}
    ]

    hoy_str = ahora.strftime("%Y-%m-%d")
    resultados = []

    for lot in loterias:
        clave = f"{hoy_str}-{hora_sorteo}-{lot['nombre']}"
        val_hash = abs(hash(clave)) % (lot["max"] + 1)
        
        num_str = "00" if val_hash == 0 and lot["max"] == 36 else f"{val_hash:02d}"
        nombre = nombres_animales.get(num_str, "Animal")

        resultados.append({
            "loteria": lot["nombre"],
            "hora": hora_sorteo,
            "numero": num_str,
            "animal": nombre
        })

    return resultados

if __name__ == "__main__":
    datos = generar_resultados()
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("Resultados generados correctamente.")
