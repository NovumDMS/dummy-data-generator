"""Authentication Routes"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.helper.ip_helper import get_ip_from_request
from app.models.auth import Users
from app.schemas import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.helper.hash_helper import hash_password, verify_password
from app.security.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db), request: Request = None):
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
        hashed_password=hashed_password,
        last_generated_by=user.username,
        last_generated_ip=get_ip_from_request(request) if request else None,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse)
def login(response: Response, credentials: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    """Login and get access token"""
    # Find user
    user = db.query(Users).filter(Users.username == credentials.username).first()
    
    if not user:
        return {
            "error": "Invalid username or password",
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    if not verify_password(credentials.password, user.hashed_password):
        user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False)
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
    user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=True)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,        # True in prod (HTTPS)
        samesite="lax",     # usually "lax"; consider "none" if cross-site
        max_age=30 * 60,
        path="/",
    )
    
    return {"message": "Login successful"}


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
