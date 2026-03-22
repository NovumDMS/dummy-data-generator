import psycopg2
import logging
from app.database import get_db
from app.models.client import Clients
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.helper.hash_helper import decrypt_db_url

logger = logging.getLogger(__name__)


def get_client_db_url(client_id: str, db: Session) -> str:
    """Retrieve client database URL"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db_url = decrypt_db_url(client.client_db_url_hash)
    return db_url


def confirm_dev_url(client_db_url: str) -> bool:
    """Confirm that the provided database URL is a development/test URL"""
    allowed_keywords = ("play", "dev", "development")
    return any(keyword in client_db_url.lower() for keyword in allowed_keywords)


def get_client_db_connection(client_id: str, db: Session) -> psycopg2.extensions.connection:
    """Connect to the client's database and return the connection URL"""
    # Get client name for logging purposes
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        logger.error(f"Client with ID {client_id} not found")
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_db_url = get_client_db_url(client_id, db)
    
    # Retrieve the hashed database URL and verify it
    if not confirm_dev_url(client_db_url):
        logger.warning(f"Attempt to connect with invalid database URL for client {client.client_name} (ID: {client_id})")
        raise HTTPException(status_code=400, detail="Invalid database URL. Only development/test URLs are allowed.")

    try:
        connection = psycopg2.connect(client_db_url)
        logger.info(f"Successfully connected to client {client.client_name} (ID: {client_id}) database")
        return connection
    except Exception as e:
        logger.error(f"Database connection error for client {client.client_name} (ID: {client_id}): {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to client's database")


def test_client_db_connection(client_id: str, db: Session) -> bool:
    """Test the connection to the client's database"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        logger.error(f"Client with ID {client_id} not found")
        raise HTTPException(status_code=404, detail="Client not found")
    connection = get_client_db_connection(client_id, db)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # Simple query to test connection
        connection.close()
        logger.info(f"Successfully connected to client {client.client_name} (ID: {client_id}) database")
        return True
    except Exception as e:
        logger.error(f"Database connection error for client {client.client_name} (ID: {client_id}): {e}")
        return False