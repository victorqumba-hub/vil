import requests
import json

try:
    response = requests.get('http://localhost:8000/api/pipeline/status')
    if response.status_code == 200:
        print("Pipeline Status API Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed to get status: {response.status_code}")
except Exception as e:
    print(f"Connection failed: {e}")
