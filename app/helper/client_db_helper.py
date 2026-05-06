import logging
from app.database import get_db
from app.models.client import Clients
from fastapi import Depends, HTTPException
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.helper.hash_helper import decrypt_db_url

logger = logging.getLogger(__name__)

def get_client_db_url(client: Clients, db: Session) -> str:
    """
    Retrieve client database URL. This pulls from the NovumDMS table not any client table.
    Requires the URL to be decrypted.

    :param client: The client object to retrieve the database URL for
    :param db: The SQLAlchemy database session. Must come from a routed method.
    :return: The decrypted database URL for the specified client
    """
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db_url = decrypt_db_url(client.client_db_url_hash)
    return db_url


def confirm_dev_url(client_db_url: str) -> bool:
    """
    Confirm that the provided database URL is a development/test URL
    :param client_db_url: The database URL to check
    :return: True if the URL is a development/test URL, False otherwise
    """
    allowed_keywords = ("play", "dev", "development", "etl")
    return any(keyword in client_db_url.lower() for keyword in allowed_keywords)


def get_client_db_connection(client_id: str, db: Session) -> sa.engine.base.Connection:
    """
    Connect to the client's database and return the connection URL
    This should be used as a context manager in a `with` statement to ensure proper cleanup, e.g.:
    with get_client_db_connection(client_id, db) as connection:
        # Use the connection here
        result = connection.execute("SELECT * FROM some_table")
        ...
    :param client_id: The ID of the client to connect to
    :param db: The SQLAlchemy database session. Must come from a routed method.
    :return: The SQLAlchemy connection to the client's database
    """
    # Get client name for logging purposes
    client = db.query(Clients).filter(Clients.id == client_id).first()
    if not client:
        logger.error(f"Client with ID {client_id} not found")
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_db_url = get_client_db_url(client, db)
    
    # Retrieve the hashed database URL and verify it
    if not confirm_dev_url(client_db_url):
        logger.warning(f"Attempt to connect with invalid database URL for client {client.client_name} (ID: {client_id})")
        raise HTTPException(status_code=400, detail="Invalid database URL. Only development/test URLs are allowed.")

    try:
        # TODO: Look into connection duplication. The engine might clean itself up, but we might be making multiple connections.
        normalized_url = client_db_url.replace("postgresql+psycopg2://", "postgresql://", 1)
        engine = sa.create_engine(normalized_url)  # Test if SQLAlchemy can create an engine with the URL
        connection = engine.connect()  # Test the connection\
        
        if connection.execute(sa.text("SELECT 1")).fetchall() is None: # Test the connection
            logger.error(f"Failed to connect to client {client.client_name} (ID: {client_id}) database")
            raise HTTPException(status_code=500, detail="Failed to connect to client's database")
        return connection
    except Exception as e:
        logger.error(f"Database connection error when connecting to client {client.client_name} (ID: {client_id}): {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to client's database")

