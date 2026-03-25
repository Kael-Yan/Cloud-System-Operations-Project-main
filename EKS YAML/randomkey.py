# generate_token.py

import secrets

def generate_secure_token():
    return secrets.token_hex(32)

if __name__ == "__main__":
    token = generate_secure_token()
    print(f"Your secure token is:\n{token}")