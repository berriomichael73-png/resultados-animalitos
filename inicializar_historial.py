import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

# Mapeo de loterías
LOTERIAS = [
    "Lotto Activo", "La Granjita", "Lotto Activo 2 (Monje Millonario)",
    "Guacharo Activo", "El Guacharito Millonario", "Selva Plus",
    "Centena Plus", "Lotto Activo Rd Int", "Mega Animal 40",
    "Centena Animalitos", "Chance Con Animalitos", "Cazaloton",
    "Ruleta Activa", "Granja Millonaria", "La-Ricachona",
    "Jungla Millonaria", "Loto Chaima", "Lotto Activo RDominicana"
]

HORARIOS = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM"]

def generar_historial_base(dias=30):
    tz_ve = timezone(timedelta(hours=-4))
    hoy = datetime.now(tz_ve)
    historial = {}

    if os.path.exists("historial_resultados.json"):
        try:
            with open("historial_resultados.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    print(f"Generando y sincronizando base de datos para los últimos {dias} días...")

    for i in range(dias):
        fecha_dt = hoy - timedelta(days=i)
        fecha_str = fecha_dt.strftime("%Y-%m-%d")

        if fecha_str in historial and len(historial[fecha_str]) > 0:
            continue

        sorteos_dia = []
        for lot in LOTERIAS:
            for hora in HORARIOS:
                sorteos_dia.append({
                    "fecha": fecha_str,
                    "loteria": lot,
                    "hora": hora,
                    "numero": "--",
                    "animal": "Por salir",
                    "imagen": "",
                    "realizado": False
                })
        
        historial[fecha_str] = sorteos_dia

    with open("historial_resultados.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

    print("Base de datos histórica inicializada con éxito.")

if __name__ == "__main__":
    generar_historial_base(30)
