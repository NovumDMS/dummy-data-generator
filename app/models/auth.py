from sqlalchemy import Column, UUID, DateTime, Integer, String

from app.database import get_db, Base, gen_uuid

db = get_db()

