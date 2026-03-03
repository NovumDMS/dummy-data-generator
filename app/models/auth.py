from sqlalchemy import Boolean, Column, UUID, DateTime, Integer, String

from app.database import get_db, Base, gen_uuid

db = get_db()

class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid(), unique=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    login_attempts = Column(Integer, default=0)
    last_login_ip = Column(String(45), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    lockout_time = Column(DateTime, nullable=True)

    def add_new_user(self, db, username: str, password_hash: str, is_admin: bool = False, is_active: bool = True):
        """Add a new user to the database"""
        new_user = Users(
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=is_active
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    