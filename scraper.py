import requests
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def obtener_resultados():
    url = "https://tuazar.com/loteria/animalitos/resultados/"
    resultados = []
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tarjetas = soup.find_all('div', class_=re.compile(f'resultado|card|block', re.I))
            
            for t in tarjetas:
                loteria = t.find(class_=re.compile(f'titulo|loteria|name', re.I))
                hora = t.find(class_=re.compile(f'hora|time', re.I))
                info = t.find(class_=re.compile(f'numero|animal|resultado', re.I))
                
                if loteria and info:
                    texto = info.get_text(strip=True)
                    match = re.search(r'(\d{1,2})\s*[-_]?\s*([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)', texto)
                    if match:
                        resultados.append({
                            "loteria": loteria.get_text(strip=True),
                            "hora": hora.get_text(strip=True) if hora else "Último",
                            "numero": match.group(1).zfill(2),
                            "animal": match.group(2).capitalize()
                        })
    except Exception as e:
        print(f"Error procesando datos: {e}")
        
    return resultados

if __name__ == "__main__":
    datos = obtener_resultados()
    if datos:
        with open("resultados.json", "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print("Resultados actualizados correctamente.")
