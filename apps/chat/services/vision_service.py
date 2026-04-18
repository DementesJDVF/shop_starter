import os
import requests
import base64
import io
from django.conf import settings
from PIL import Image

# Configuración de Groq
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

def analyze_image_for_search(image_file, is_url=False):
    """
    Procesa una imagen y extrae parámetros de búsqueda descriptivos
    usando Groq Llama 4 Scout.
    """
    if not GROQ_API_KEY:
        return {"error": "Falta configuración de GROQ_API_KEY."}

    try:
        if is_url:
            response = requests.get(image_file)
            img = Image.open(io.BytesIO(response.content))
        else:
            if hasattr(image_file, 'read'):
                img = Image.open(image_file)
                image_file.seek(0)
            else:
                img = Image.open(image_file)

        # Redimensionar para optimizar uso de la API (1024x1024 max)
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analiza esta imagen de un producto. Tu objetivo es ayudar a una base de datos a encontrar productos similares. Genera una lista corta de 3 a 5 palabras clave precisas que describan el producto principal (ej: 'reloj de cuero analógico', 'zapatillas deportivas rojas', 'bolso negro elegante'). Responde ÚNICAMENTE con los términos separados por comas."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.2,
            "max_tokens": 100
        }

        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            description = result['choices'][0]['message']['content']
            return {"keywords": description.strip()}
        else:
            error_data = response.json() if response.status_code != 500 else {}
            print(f"Error Groq Vision API {response.status_code}: {error_data}")
            return {"error": f"Fallo al procesar imagen en Groq ({response.status_code})"}

    except Exception as e:
        print(f"Excepción en vision_service: {str(e)}")
        return {"error": "Error interno al procesar formato de imagen."}
