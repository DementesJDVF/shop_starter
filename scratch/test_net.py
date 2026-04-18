import requests
try:
    res = requests.post("https://httpbin.org/post", json={"test": "ok"})
    print(f"HTTPBin Status: {res.status_code}")
    print(f"HTTPBin Response: {res.text[:100]}")
except Exception as e:
    print(f"Error: {e}")
