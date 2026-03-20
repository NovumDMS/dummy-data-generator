import os
from passlib.context import CryptContext
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv('working.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _password_pepper():
    p = os.getenv("PASSWORD_PEPPER")
    if not p:
        raise RuntimeError("PASSWORD_PEPPER environment variable is not set")
    return p

def hash_password(password: str) -> str:
    """Hash a password with pepper"""
    pepper = _password_pepper()
    peppered_password = password + pepper
    return pwd_context.hash(peppered_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    peppered_password = plain_password + _password_pepper()
    return pwd_context.verify(peppered_password, hashed_password)

def encrypt_db_url(db_url: str) -> str:
    """Encrypt a database URL"""
    if db_url is None:
        raise ValueError("Database URL cannot be None")
    fernet_key = os.getenv("FERNET_SECRET_KEY")
    if not fernet_key:
        raise RuntimeError("FERNET_SECRET_KEY environment variable is not set")
    fernet = Fernet(fernet_key.encode())
    encrypted_url = fernet.encrypt(db_url.encode()).decode()
    return encrypted_url

def decrypt_db_url(encrypted_url: str) -> str:
    """Decrypt a database URL"""
    fernet_key = os.getenv("FERNET_SECRET_KEY")
    if not fernet_key:
        raise RuntimeError("FERNET_SECRET_KEY environment variable is not set")
    fernet = Fernet(fernet_key.encode())
    decrypted_url = fernet.decrypt(encrypted_url.encode()).decode()
    return decrypted_url