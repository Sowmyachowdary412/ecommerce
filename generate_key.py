import secrets
import base64
from datetime import datetime

def generate_secret_key():
    """Generate a secure secret key"""
    # Generate a random 32-byte key
    return secrets.token_urlsafe(32)

def create_env_file(secret_key):
    """Create .env file with generated keys"""
    env_content = f"""# Generated on {datetime.now()}
                    SECRET_KEY={secret_key}
                    ALGORITHM=HS256
                    ACCESS_TOKEN_EXPIRE_MINUTES=30
                    """
    with open('.env', 'w') as f:
        f.write(env_content)

if __name__ == "__main__":
    try:
        # Generate secret key
        secret_key = generate_secret_key()
        
        # Create .env file
        create_env_file(secret_key)
        
        print("\nSecret key generated successfully!")
        print("\nGenerated Secret Key:")
        print(secret_key)
        print("\n.env file has been created with the following contents:")
        with open('.env', 'r') as f:
            print(f.read())
            
    except Exception as e:
        print(f"Error generating key: {e}")