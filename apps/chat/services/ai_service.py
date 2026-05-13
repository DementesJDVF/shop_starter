import os
import requests
import json
from django.conf import settings

GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Para texto rápido y parámetros, llama-3.3-70b-versatile es excelente y rápido
GROQ_MODEL = "llama-3.3-70b-versatile"

def extract_search_parameters(user_message, image_keywords=None):
    """
    Analiza el mensaje del usuario y las palabras clave de la imagen (si existen)
    para extraer parámetros de búsqueda estructurados.
    Devuelve un diccionario.
    """
    if not GROQ_API_KEY:
        return {"keywords": user_message, "max_price": None}

    system_prompt = """Eres un asistente extractor de parámetros de e-commerce.
Analiza la intención del usuario. Si hay contexto de imagen, incorpóralo para mejorar la búsqueda.
Tu salida DEBE SER ÚNICAMENTE texto JSON válido (sin markdown, sin bloques de código) con estas claves:
- "keywords": string (palabras principales a buscar, resumen).
- "max_price": float o null (presupuesto máximo detectado).
Ejemplo: {"keywords": "zapatillas deportivas rojas", "max_price": 50.0}"""

    context_msg = f"Mensaje del usuario: {user_message}"
    if image_keywords:
        context_msg += f"\nContexto de imagen adjunta: {image_keywords}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_msg}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            parsed = json.loads(content)
            return {
                "keywords": parsed.get("keywords", user_message),
                "max_price": parsed.get("max_price")
            }
        else:
            return {"keywords": user_message, "max_price": None}
    except Exception as e:
        print(f"Error extrayendo parámetros: {str(e)}")
        return {"keywords": user_message, "max_price": None}

def generate_chat_response(user_message, products_data, image_keywords=None):
    """
    El asistente principal responde al usuario con base en los productos encontrados en la base de datos.
    """
    if not GROQ_API_KEY:
        return "Disculpa, el servicio de inteligencia artificial no está disponible en este momento."

    system_prompt = """Eres un experto vendedor de ShopStarter (aplicación Geo), sumamente persuasivo, amable y servicial.
Responde siempre en español. Usa emojis para ser amigable.
Tu objetivo es ayudar al cliente a encontrar lo que busca usando ÚNICAMENTE el contexto de productos encontrado en la base de datos.
Menciona por qué el producto recomendado es ideal, pero sé breve (máximo 2 o 3 párrafos).
Si no se encontraron productos, dile amablemente que no hay coincidencias exactas y sugiérele probar otra búsqueda."""

    context_msg = f"Mensaje del cliente: {user_message}\n"
    if image_keywords:
        context_msg += f"[El cliente adjuntó una imagen que el sistema describe como: {image_keywords}]\n"
        
    context_msg += f"\nPRODUCTOS DISPONIBLES EN DB:\n{json.dumps(products_data, ensure_ascii=False)}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_msg}
        ],
        "temperature": 0.6,
        "max_tokens": 512
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Error Chat API: {response.text}")
            return "Lo siento, tuve un problema analizando tus productos."
    except Exception as e:
        print(f"Excepción en Chat API: {str(e)}")
        return "Parece que hay un retraso en la conexión en este momento."
