"""Authentication Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auth import Users
from app.schemas import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.security import hash_password, verify_password
from app.security.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(Users).filter(
        (Users.username == user.username) | (Users.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = Users(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Find user
    user = db.query(Users).filter(Users.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        return {
            "error": "Invalid username or password",
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    if not user.is_active:
        return {
            "error": "User account is inactive",
            "status_code": status.HTTP_403_FORBIDDEN
        }
    
    # Create access token
    access_token = create_access_token({"sub": user.username, "user_id": user.id})
    
    return {"access_token": access_token}


@router.get("/me", response_model=UserResponse)
def get_current_user(token: str = None, db: Session = Depends(get_db)):
    """Get current user info (requires authentication)"""
    # This is a placeholder - implement full token verification in production
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )
