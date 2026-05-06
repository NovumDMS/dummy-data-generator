from datetime import datetime, timezone
import os
from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, UUID, DateTime, Integer, String

from app.database import Base, gen_uuid
from app.helper.hash_helper import encrypt_db_url, decrypt_db_url

def check_client_db_whitelist(client_db_url: str) -> bool:
    """Check if the client's database URL is in the whitelist"""
    # TODO: We need to create the whitelist
    whitelist = [url.strip() for url in os.getenv("CLIENT_DB_LIST", "").split(",") if url.strip()]
    return client_db_url in whitelist

class Clients(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, index=True)
    client_id = Column(String(3), unique=True, index=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_db_url_hash = Column(String(255), nullable=False)
    generation_count = Column(Integer, default=0)
    last_generated_ip = Column(String(45), nullable=True)
    last_generated_by = Column(String(255), nullable=True)
    last_generated_at = Column(DateTime, nullable=True)
    deleted_flag = Column(Boolean, default=False)  # 0 for active, 1 for deleted TODO: Probably unnecessary
    email = Column(String(255), nullable=True)

    @staticmethod
    def add_new_client(db, client_id: str, client_name: str, client_db_url: str, email: str = None, last_generated_by: str = None, last_generated_ip: str = None):
        """Add a new client to the database"""
        allowed_keywords = ("play", "dev", "development", "etl")
        if any(keyword in client_db_url.lower() for keyword in allowed_keywords):  # Allow only development/test database URLs
            client_db_url_hash = encrypt_db_url(client_db_url)

            new_client = Clients(
                id=gen_uuid(),
                client_id=client_id,
                client_name=client_name,
                client_db_url_hash=client_db_url_hash,
                last_generated_by=last_generated_by,
                last_generated_ip=last_generated_ip,
                last_generated_at=datetime.now(timezone.utc),
                email=email
            )
            db.add(new_client)
            db.commit()
            db.refresh(new_client)
            return new_client
        else:
            raise ValueError("Invalid database URL. Only development/test URLs are allowed.")
        
    @staticmethod
    def check_client_db_url(db, client_id: str) -> bool:
        """Check if the provided client database URL matches the stored hash"""
        client = db.query(Clients).filter(Clients.id == client_id).first()
        if not client:
            return False
        
        return decrypt_db_url(client.client_db_url_hash)

    def log_client_generation(
            self, 
            db, 
            client_id: str, 
            generated_by: str, 
            generated_ip: str):
        """Log client generation activity"""
        client = db.query(Clients).filter(Clients.id == client_id).first()
        if not client:
            return None
        
        client.generation_count += 1
        client.last_generated_by = generated_by
        client.last_generated_ip = generated_ip
        client.last_generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(client)
        return client
