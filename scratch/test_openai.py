import requests
import os

def test_openai():
    # Key from user's .env (read in previous view_file)
    KEY = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {KEY}"}
    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "say hi"}],
                "max_tokens": 10
            }
        )
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openai()
