import psycopg2
from sqlalchemy import UUID
from app.database import get_db
from app.models.client import Clients
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.helper.hash_helper import decrypt_db_url

def get_client_db_url(client_id: str, db: Session = Depends(get_db)) -> str:
    """Retrieve client database URL"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.db_url

def confirm_dev_url(client_db_url: str) -> bool:
    """Confirm that the provided database URL is a development/test URL"""
    allowed_keywords = ("play", "dev", "development")
    return any(keyword in client_db_url.lower() for keyword in allowed_keywords)

def get_client_db_connection(client_id: str, db: Session = Depends(get_db)) -> str:
    """Connect to the client's database and return the connection URL"""
    client_db_url_hash = get_client_db_url(client_id, db)
    
    client_db_url = decrypt_db_url(client_db_url_hash)
    
    # Retrieve the hashed database URL and verify it
    if not confirm_dev_url(client_db_url):
        raise HTTPException(status_code=400, detail="Invalid database URL. Only development/test URLs are allowed.")
    # If verification is successful, return the original database URL

    return psycopg2.connect(client_db_url)