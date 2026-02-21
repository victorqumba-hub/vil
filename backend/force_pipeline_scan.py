import json
import urllib.request
import urllib.parse
import urllib.error

# Constants
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/login"
PIPELINE_URL = f"{BASE_URL}/api/pipeline/run"
EMAIL = "demo@vil.io"
PASSWORD = "password123"

def post_json(url, data, headers=None):
    if headers is None: headers = {}
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers={
        'Content-Type': 'application/json',
        **headers
    })
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

def post_form(url, data):
    form_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=form_data, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def force_scan():
    print("--- Forcing Pipeline Scan (urllib) ---")
    
    # 1. Login
    print(f"Logging in as {EMAIL}...")
    status, body = post_json(LOGIN_URL, {"email": EMAIL, "password": PASSWORD}) # JSON body, note fields 'email' not 'username' based on LoginRequest schema usually
    if status != 200:
        print(f"Login failed: {status} - {body}")
        return
    token = body["access_token"]
    print("Login successful.")

    # 2. Trigger Pipeline
    print("Triggering pipeline/run...")
    headers = {"Authorization": f"Bearer {token}"}
    # symbols is body (List[str]), top_n is query param
    url_with_params = f"{PIPELINE_URL}?top_n=10"
    status, body = post_json(url_with_params, [], headers) # Send empty list for 'symbols'
    
    if status == 200:
        count = body.get("count", 0)
        print(f"SUCCESS: Pipeline run complete.")
        print(f"Generated {count} signals.")
        if count > 0:
            print("First signal sample:", json.dumps(body["signals"][0], indent=2))
        else:
            print("WARNING: 0 signals generated.")
    else:
        print(f"Pipeline call failed: {status} - {body}")

    # 3. Check Persistence (GET /api/signals/live)
    print("\nChecking persistence (GET /api/signals/live)...")
    SIGNAL_URL = f"{BASE_URL}/api/signals/live"
    status, body = post_json(SIGNAL_URL, {}, headers) # Actually GET, but let's see if post_json can be adapted or use urllib.request directly
    
    # helper for GET
    req = urllib.request.Request(SIGNAL_URL, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            signals = json.loads(response.read().decode())
            print(f"API Returned {len(signals)} live signals.")
            if len(signals) > 0:
                print("Sample Signal:", json.dumps(signals[0], indent=2))
            else:
                print("WARNING: API returned 0 signals despite successful scan.")
    except Exception as e:
        print(f"GET failed: {e}")

if __name__ == "__main__":
    force_scan()
