from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.client import Clients
from app.schemas import ClientCreate
from app.security.access import admin_required, login_required

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/")
@login_required
@admin_required
def get_clients(db: Session = Depends(get_db)):
    """Get all clients"""
    clients = db.query(Clients).all()
    return clients

@router.post("/register")
@login_required
@admin_required
def register_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Register a new client"""
    try:
        Clients.add_new_client(db, client.client_id, client.client_name, client.client_db_url_hash)
    except ValueError as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return {
        "message": "Client registered successfully",
        "client_id": client.client_id,
        "status_code": status.HTTP_201_CREATED
    }