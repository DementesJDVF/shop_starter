import os
import requests

API_URL = "https://api-inference.huggingface.co/models/vikhyatk/moondream2"
TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def query():
    # Test Moondream2 specifically
    print(f"Testing {API_URL}...")
    # Moondream2 often expects JSON with 'inputs' (image) or raw binary
    res = requests.post(API_URL, headers=headers, data=b"dummy")
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:300]}")

if __name__ == "__main__":
    query()
