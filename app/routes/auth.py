"""Authentication Routes"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.helper.ip_helper import get_ip_from_request
from app.models.auth import Users
from app.schemas import UserCreate, LoginRequest, TokenResponse
from app.helper.hash_helper import hash_password, verify_password
from app.security.jwt import create_access_token
from app.security.access import admin_required, login_required, _redirect_to_login

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@login_required
@admin_required
def register(user: UserCreate, db: Session = Depends(get_db), request: Request = None):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(Users).filter(
        (Users.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"  
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = Users.add_new_user(db=db, username=user.username, password_hash=hashed_password, is_admin=True)
    return db_user


@router.post("/login")
def login(response: Response, credentials: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    """Login and get access token"""
    # Find user
    user = db.query(Users).filter(Users.username == credentials.username).first()
    
    if not user:
        return {
            "error": "Invalid username or password",
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    if not verify_password(credentials.password, user.password_hash):
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
    access_token = create_access_token({"sub": user.username, "user_id": str(user.id), "is_admin": user.is_admin})
    user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=True)

    is_secure_cookie = os.getenv("ENVIRONMENT", "DEV").upper() == "PROD"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure_cookie,
        samesite="lax",     # usually "lax"; consider "none" if cross-site
        max_age=30 * 60,
        path="/",
    )
    
    return {"message": "Login successful"}

@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    """Logout user by clearing the access token cookie"""
    redirect_response = _redirect_to_login(request, "Logged out successfully", "success")
    redirect_response.delete_cookie(key="access_token", path="/")
    return redirect_response
