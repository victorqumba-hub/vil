import urllib.request
import json
import time

BASE_URL = "http://localhost:8000/api"

def post(url, data=None, headers=None):
    if headers is None: headers = {}
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data_bytes = None
    
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        print(f"Error {url}: {e}")
        try:
            errors = e.read().decode('utf-8')
            print(f"Details: {errors}")
        except: pass
        return None

def test():
    print(f"Logging in to {BASE_URL}...")
    token_resp = post(f"{BASE_URL}/login", {"email": "demo@vil.io", "password": "password123"})
    if not token_resp:
        print("Login failed.")
        return
    
    token = token_resp.get("access_token")
    if not token:
        print("No access token returned.")
        return
    print("Got access token.")

    print("Triggering pipeline run (this may take a few seconds)...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Run pipeline
    start = time.time()
    res = post(f"{BASE_URL}/pipeline/run", None, headers)
    duration = time.time() - start
    
    if res:
        count = res.get('count', 0)
        print(f"Pipeline run successful in {duration:.2f}s!")
        print(f"Generated {count} signals.")
        
        signals = res.get('signals', [])
        classes = set(s.get('asset_class') for s in signals)
        print(f"Asset classes found in output: {classes}")
        
        # Check specific classes
        expected = {'forex', 'index', 'commodity', 'metal', 'crypto'}
        missing = expected - classes
        if not missing:
            print("✅ All asset classes present!")
        else:
            print(f"⚠️ Missing asset classes: {missing} (Maybe market conditions didn't trigger signals?)")
            
    else:
        print("Pipeline run failed.")

if __name__ == "__main__":
    test()
