from sqlalchemy import Column, UUID, DateTime, Integer, String

from app.database import get_db, Base, gen_uuid

db = get_db()

class Clients(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid(), unique=True, index=True)
    client_id = Column(String(3), unique=True, index=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_db_url_hash = Column(String(255), nullable=False)
    generation_count = Column(Integer, default=0)
    last_accessed_ip = Column(String(45), nullable=True)
    last_accessed_by = Column(String(255), nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)