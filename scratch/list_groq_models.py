import requests
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def list_models():
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        models = res.json().get('data', [])
        ids = [m['id'] for m in models]
        print("\n".join(sorted(ids)))
    else:
        print(f"Error {res.status_code}: {res.text}")

if __name__ == "__main__":
    list_models()
