import asyncio
import sys
import os
import httpx

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.config import settings

async def main():
    print("Checking OANDA Configuration...")
    print(f"API Key present: {bool(settings.OANDA_API_KEY)}")
    print(f"Account ID configured: {settings.OANDA_ACCOUNT_ID}")
    print(f"Environment: {settings.OANDA_ENV}")

    if not settings.OANDA_API_KEY:
        print("Error: OANDA_API_KEY is missing.")
        return

    base_url = (
        "https://api-fxtrade.oanda.com/v3"
        if settings.OANDA_ENV == "live"
        else "https://api-fxpractice.oanda.com/v3"
    )
    headers = {
        "Authorization": f"Bearer {settings.OANDA_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"\nTesting connection to {base_url}...")
    
    # 1. Check Accounts List
    print("\n--- Listing Accounts ---")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{base_url}/accounts", headers=headers)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                accounts = data.get("accounts", [])
                print(f"Found {len(accounts)} accounts:")
                found_configured = False
                for acc in accounts:
                    print(f" - ID: {acc['id']} Tags: {acc.get('tags', [])}")
                    if acc['id'] == settings.OANDA_ACCOUNT_ID:
                        found_configured = True
                
                if found_configured:
                    print(f"\nSUCCESS: Configured Account ID {settings.OANDA_ACCOUNT_ID} found in account list.")
                else:
                    print(f"\nWARNING: Configured Account ID {settings.OANDA_ACCOUNT_ID} NOT found in account list.")
            else:
                print(f"Error listing accounts: {resp.text}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Exception listing accounts: {e}")

    # 2. Check Account Details (if configured)
    if settings.OANDA_ACCOUNT_ID:
        print(f"\n--- Checking Details for Account {settings.OANDA_ACCOUNT_ID} ---")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{base_url}/accounts/{settings.OANDA_ACCOUNT_ID}", headers=headers, timeout=30.0)
                print(f"Status Code: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    acc = data.get("account", {})
                    print(f"Account Currency: {acc.get('currency')}")
                    print(f"Balance: {acc.get('balance')}")
                    print(f"NAV: {acc.get('NAV')}")
                    print("SUCCESS: Account details fetched.")
                else:
                    print(f"Error fetching account details: {resp.text}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Exception fetching account details: {e}")

if __name__ == "__main__":
    asyncio.run(main())
