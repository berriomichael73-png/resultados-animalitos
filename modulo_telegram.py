import re
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto
import pytesseract
from PIL import Image
import io

# Credenciales de Telegram API (se obtienen en my.telegram.org)
API_ID = 12345678  # Reemplazar con tu API_ID de Telegram
API_HASH = "tu_api_hash_aqui"  # Reemplazar con tu API_HASH

CANALES_LOTERIAS = [
    "@ResultadosLottoActivoOficial",
    "@LaGranjitaOficialResultados",
    "@AnimalitosEnVivoVE"
]

def extraer_datos_de_texto(texto):
    # Detecta patrones tipo "10:00 AM - 18 BURRO" o "08:00 AM: 28 ZAMURO"
    match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[-:]?\s*(\d{1,2})\s*[-:]?\s*([A-Za-z]+)', texto, re.IGNORECASE)
    if match:
        return {
            "hora": match.group(1).upper(),
            "numero": match.group(2).zfill(2),
            "animal": match.group(3).upper()
        }
    return None

def obtener_resultados_telegram():
    resultados = []
    try:
        with TelegramClient('session_nexus', API_ID, API_HASH) as client:
            for canal in CANALES_LOTERIAS:
                for message in client.iter_messages(canal, limit=5):
                    if message.text:
                        datos = extraer_datos_de_texto(message.text)
                        if datos:
                            resultados.append(datos)
                    elif message.media and isinstance(message.media, MessageMediaPhoto):
                        # Si enviaron una imagen con el resultado, aplicamos OCR
                        image_bytes = client.download_media(message.media, file=bytes)
                        img = Image.open(io.BytesIO(image_bytes))
                        texto_ocr = pytesseract.image_to_string(img)
                        datos = extraer_datos_de_texto(texto_ocr)
                        if datos:
                            resultados.append(datos)
    except Exception as e:
        print(f"Error consultando Telegram: {e}")
    return resultados

if __name__ == "__main__":
    res = obtener_resultados_telegram()
    print("Resultados capturados desde Telegram:", res)
