import httpx
import json
import asyncio

BASE_URL = "http://127.0.0.1:8000"

async def trigger_manual_scan():
    print("--- TRIGGERING MANUAL VIL PIPELINE SCAN ---")
    
    # 1. Login to get token
    login_url = f"{BASE_URL}/api/login"
    login_payload = {"email": "demo@vil.io", "password": "DemoTrader@2026"}
    
    async with httpx.AsyncClient() as client:
        try:
            login_res = await client.post(login_url, json=login_payload)
            login_res.raise_for_status()
            token = login_res.json()["access_token"]
            print("Authenticated successfully.")
        except Exception as e:
            print(f"Login failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # 2. Trigger Pipeline
        run_url = f"{BASE_URL}/api/pipeline/run"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "symbols": ["EUR_USD", "XAU_USD", "BTC_USD"],
            "timeframe": "H1",
            "top_n": 3
        }
        
        print(f"Triggering scan for {payload['symbols']}...")
        try:
            # The API endpoint expects a JSON body.
            run_res = await client.post(run_url, json=payload, headers=headers, timeout=120)
            run_res.raise_for_status()
            data = run_res.json()
            print(f"Scan completed. Generated {data['count']} signals.")
            for s in data["signals"]:
                print(f" - {s['symbol']}: Score {s.get('score', 0):.1f} | Status: {s.get('status')}")
        except Exception as e:
            print(f"Pipeline trigger failed: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_manual_scan())
