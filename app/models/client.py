from sqlalchemy import Column, UUID, DateTime, Integer, String

from app.database import get_db, Base, gen_uuid
from app.helper.hash_helper import hash_db_url

db = get_db()

class Clients(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid(), unique=True, index=True)
    client_id = Column(String(3), unique=True, index=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_db_url_hash = Column(String(255), nullable=False)
    generation_count = Column(Integer, default=0)
    last_generated_ip = Column(String(45), nullable=True)
    last_generated_by = Column(String(255), nullable=True)
    last_generated_at = Column(DateTime, nullable=True)

    def add_new_client(self, db, client_id: str, client_name: str, client_db_url: str):
        """Add a new client to the database"""
        if "play" in client_db_url or "dev" in client_db_url or "development" in client_db_url: # Check to ensure development/test database URL            
            client_db_url_hash = hash_db_url(client_db_url)

            new_client = Clients(
                client_id=client_id,
                client_name=client_name,
                client_db_url_hash=client_db_url_hash
            )
            db.add(new_client)
            db.commit()
            db.refresh(new_client)
            return new_client
        else:
            raise ValueError("Invalid database URL. Only development/test URLs are allowed.")