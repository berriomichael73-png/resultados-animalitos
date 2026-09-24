import cv2
import pytesseract
import re
from PIL import Image

def analizar_frame_transmision(url_stream_video):
    cap = cv2.VideoCapture(url_stream_video)
    if not cap.isOpened():
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    # Preprocesamiento de la imagen para mejorar el OCR
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Convertir a imagen PIL y extraer texto con Tesseract
    pil_img = Image.fromarray(thresh)
    texto_detectado = pytesseract.image_to_string(pil_img)

    # Buscar coincidencia de número y animal
    match = re.search(r'(\d{1,2})\s*[-:]?\s*([A-Za-z]+)', texto_detectado)
    if match:
        return {
            "numero": match.group(1).zfill(2),
            "animal": match.group(2).upper()
        }
    return None
