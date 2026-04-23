import os
from passlib.context import CryptContext
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv('working.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _password_pepper():
    """Retrieve the password pepper from environment variables"""
    p = os.getenv("PASSWORD_PEPPER")
    if not p:
        raise RuntimeError("PASSWORD_PEPPER environment variable is not set")
    return p

def hash_password(password: str) -> str:
    """
    Hash a password with pepper
    :param password: The plain text password to hash
    :return: The hashed password
    """
    pepper = _password_pepper()
    peppered_password = password + pepper
    return pwd_context.hash(peppered_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    :param plain_password: The plain text password to verify
    :param hashed_password: The hashed password to compare against
    :return: True if the password matches, False otherwise
    """
    peppered_password = plain_password + _password_pepper()
    return pwd_context.verify(peppered_password, hashed_password)

def encrypt_db_url(db_url: str) -> str:
    """
    Encrypt a database URL. This uses Fernet to encrypt the url
    to store in Novum database securely.
    :param db_url: The database URL to encrypt
    :return: The encrypted database URL
    """
    if db_url is None:
        raise ValueError("Database URL cannot be None")
    fernet_key = os.getenv("FERNET_SECRET_KEY")
    if not fernet_key:
        raise RuntimeError("FERNET_SECRET_KEY environment variable is not set")
    fernet = Fernet(fernet_key.encode())
    encrypted_url = fernet.encrypt(db_url.encode()).decode()
    return encrypted_url

def decrypt_db_url(encrypted_url: str) -> str:
    """
    Decrypt a database URL. This uses Fernet to decrypt the url
    stored in Novum database securely.
    :param encrypted_url: The encrypted database URL to decrypt
    :return: The decrypted database URL
    """
    fernet_key = os.getenv("FERNET_SECRET_KEY")
    if not fernet_key:
        raise RuntimeError("FERNET_SECRET_KEY environment variable is not set")
    fernet = Fernet(fernet_key.encode())
    decrypted_url = fernet.decrypt(encrypted_url.encode()).decode()
    return decrypted_url