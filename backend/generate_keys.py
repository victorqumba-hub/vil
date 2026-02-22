import secrets

def generate_keys():
    jwt_secret = secrets.token_urlsafe(32)
    encryption_key = secrets.token_hex(32) # 64 chars (32 bytes)
    
    print("--- PRODUCTION SECURITY KEYS ---")
    print(f"JWT_SECRET_KEY: {jwt_secret}")
    print(f"CREDENTIAL_ENCRYPTION_KEY: {encryption_key}")
    print("--------------------------------")
    print("Copy these into your Render / Vercel environment variables.")

if __name__ == "__main__":
    generate_keys()
