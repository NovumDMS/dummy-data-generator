import os
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv('working.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _db_url_pepper():
    p = os.getenv("URL_PEPPER")
    if not p:
        raise RuntimeError("URL_PEPPER environment variable is not set")
    return p

def _password_pepper():
    p = os.getenv("PASSWORD_PEPPER")
    if not p:
        raise RuntimeError("PASSWORD_PEPPER environment variable is not set")
    return p

def hash_password(password: str) -> str:
    """Hash a password with pepper"""
    pepper = _password_pepper()
    peppered_password = password + pepper
    print(f"Hashing password: {password} with pepper: {peppered_password}")
    return pwd_context.hash(peppered_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    peppered_password = plain_password + _password_pepper()
    return pwd_context.verify(peppered_password, hashed_password)

def hash_db_url(db_url: str) -> str:
    """Hash a database URL with pepper"""
    peppered_url = db_url + _db_url_pepper()
    return pwd_context.hash(peppered_url)

def verify_db_url(plain_db_url: str, hashed_db_url: str) -> bool:
    """Verify a database URL against its hash"""
    peppered_url = plain_db_url + _db_url_pepper()
    return pwd_context.verify(peppered_url, hashed_db_url)