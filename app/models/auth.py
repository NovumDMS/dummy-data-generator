from datetime import datetime, timedelta, timezone

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

    @staticmethod
    def add_new_user(db, username: str, password_hash: str, is_admin: bool = False, is_active: bool = True):
        """Add a new user to the database"""
        new_user = Users(
            id=gen_uuid(),
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=is_active
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def track_user_login( 
            db, 
            user_id: UUID, 
            login_ip: str, 
            successful: bool = True, 
            max_login_attempts: int = 5, 
            lockout_duration_minutes: int = 30):
        """Track user login attempts and lock account if necessary"""
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            return None
        
        if successful:
            user.login_attempts = 0
            user.last_login_ip = login_ip
            user.last_login_at = datetime.now(timezone.utc)
        else:
            user.login_attempts += 1
            if user.login_attempts >= max_login_attempts:
                user.lockout_time = datetime.now(timezone.utc) + timedelta(minutes=lockout_duration_minutes)
        
        db.commit()
        db.refresh(user)
        return user