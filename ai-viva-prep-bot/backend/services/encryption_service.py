from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY", "")

if not FERNET_KEY:
    FERNET_KEY = Fernet.generate_key().decode()
    print(f"WARNING: No FERNET_KEY in .env. Generated temporary key: {FERNET_KEY}")
    print("Add this to your .env file as FERNET_KEY= to persist encrypted data across restarts.")

_fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)


def encrypt_value(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    return _fernet.decrypt(encrypted_value.encode()).decode()
