import os
import requests
import base64
import io
from django.conf import settings
from PIL import Image

# Configuración de claves
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))

# Endpoint de Groq
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Modelo Vision de Groq (Llama 3.2 Vision - El más rápido y estable)
GROQ_MODEL = "llama-3.2-11b-vision-preview"

def generate_product_description(image_file_path_or_url, is_url=False):
    """
    Toma una imagen, la redimensiona y usa Groq (Llama 3.2 Vision) 
    para generar una descripción técnica y llamativa en español.
    """
    if not GROQ_API_KEY:
        return "Configuración incompleta: Falta el GROQ_API_KEY en el servidor."

    try:
        # 1. Obtener imagen
        if is_url:
            response = requests.get(image_file_path_or_url, timeout=15)
            img = Image.open(io.BytesIO(response.content))
        else:
            if hasattr(image_file_path_or_url, 'read'):
                img = Image.open(image_file_path_or_url)
                image_file_path_or_url.seek(0)
            else:
                img = Image.open(image_file_path_or_url)
                image_file_path_or_url.seek(0) # Reset pointer

        # 2. Procesar imagen (Redimensionar para ahorrar tokens y evitar errores 400)
        # Groq y la mayoría de las IAs prefieren máx 1024 o 1536 px, pero 800 es ideal para latencia
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convertir a RGB si es necesario (ej: PNG transparente a JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # 3. Guardar en memoria como JPEG comprimido (Calidad 60 para máxima velocidad)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # 4. Preparar la petición para Groq
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
                            "text": "Eres un experto en marketing digital. Describe el producto de la imagen de forma técnica, sumamente llamativa y elegante (MÁXIMO 20 PALABRAS). Enfócate en calidad y beneficios. Responde solo con el texto de la descripción en español, sin preámbulos ni comentarios."
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
            "temperature": 0.5,
            "max_tokens": 1024
        }

        # 5. Llamar a Groq
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            description = result['choices'][0]['message']['content']
            return description.strip()
        else:
            error_data = response.json() if response.status_code != 500 else {"error": {"message": "Internal Server Error"}}
            error_msg = error_data.get('error', {}).get('message', 'Error desconocido')
            print(f"Error Groq API {response.status_code}: {error_msg}")
            return f"Hubo un detalle con la IA ({response.status_code}). Intenta con otra imagen o espera un segundo."

    except Exception as e:
        print(f"Excepción en AI Service: {str(e)}")
        return "No pudimos procesar la imagen. Asegúrate de que sea un formato válido (JPG, PNG)."
