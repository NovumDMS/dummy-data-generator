import os
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.client import Clients
from app.schemas import ClientCreate
from app.security.access import login_required
from app.helper.client_db_helper import get_client_db_connection, test_client_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/")
@login_required
def get_clients(request: Request, response: Response, db: Session = Depends(get_db)):
    """Get all clients"""
    clients = db.query(Clients).all()
    return clients

@router.post("/register")
@login_required
def register_client(client: ClientCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Register a new client"""
    existing_client = db.query(Clients).filter(Clients.client_id == client.client_id).first()
    if existing_client:
        logger.warning(f"Registration attempt with existing client ID: {client.client_id} from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID already registered"  
        )
    
    Clients.add_new_client(db, client.client_id, client.name, client.db_url, email=client.email)
    return {
        "message": "Client registered successfully"
    }

@router.delete("/{client_id}")
@login_required
def delete_client(client_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """Delete a client by ID"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    db.delete(client)
    db.commit()
    return {
        "message": "Client deleted successfully",
        "client_id": client_id
    }

@router.get("/client-info/{client_id}")
@login_required
def get_client_info(client_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """Get information about a specific client by ID"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.get("/{client_id}/data")
@login_required
def get_client_data(client_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """Get client data for a specific client by ID"""
    client = db.query(Clients).filter(Clients.client_id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    try:
        connection = get_client_db_connection(client_id, db)
        with connection.cursor() as cursor:
            if not test_client_db_connection(client_id, db):
                logger.warning(f"Failed connection test for client {client.client_name} (ID: {client_id}) from IP: {request.client.host}")
                raise HTTPException(status_code=400, detail="Failed to connect to client's database. Please check the database URL and try again.")

            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            return {"tables": [table[0] for table in tables]}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Database connection error for client {client.client_name} (ID: {client_id}): {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve client data")