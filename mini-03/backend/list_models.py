import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

print(f"Testing key: {API_KEY[:5]}...{API_KEY[-5:]}")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("\nAvailable Models:")
        for m in models:
            print(f"- {m['name']} (Supported: {m['supportedGenerationMethods']})")
    else:
        print(f"\nError {response.status_code}: {response.text}")

except Exception as e:
    print(f"Error: {e}")
