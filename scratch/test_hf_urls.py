import os
import requests

TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
headers = {"Authorization": f"Bearer {TOKEN}"}

urls = [
    "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
    "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning",
    "https://api-inference.huggingface.co/models/gpt2"
]

def test():
    for url in urls:
        print(f"Testing {url}...")
        try:
            # Try GET first to see if model exists
            res_get = requests.get(url, headers=headers)
            print(f"  GET Status: {res_get.status_code}")
            
            # Try POST
            res_post = requests.post(url, headers=headers, json={"inputs": "test"})
            print(f"  POST Status: {res_post.status_code}")
            if res_post.status_code == 404:
                print(f"  POST Error: {res_post.text[:50]}")
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    test()
