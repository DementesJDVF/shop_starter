import os
import django
import sys
import requests

# Configurar entorno Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.conf import settings

def test_llama4_vision():
    print("--- PROBANDO LLAMA 4 SCOUT VISION ---")
    api_key = getattr(settings, 'GROQ_API_KEY', None)
    model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    if not api_key:
        print("ERROR: GROQ_API_KEY no encontrada.")
        return

    from PIL import Image
    import io
    import base64
    
    img = Image.new('RGB', (100, 100), color='blue')
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    b64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                    }
                ]
            }
        ],
        "max_tokens": 50
    }

    try:
        print(f"DEBUG: Enviando peticion con modelo {model}...")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        
        print(f"STATUS CODE: {response.status_code}")
        if response.status_code == 200:
            print("EXITO: El nuevo modelo respondio correctamente.")
            print("RESPUESTA:", response.json()['choices'][0]['message']['content'])
        else:
            print("FALLO:")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_llama4_vision()
