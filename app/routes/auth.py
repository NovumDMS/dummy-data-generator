"""Authentication Routes"""
from datetime import datetime, timezone
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.helper.ip_helper import get_ip_from_request
from app.models.auth import Users
from app.models.logging import AuthenticationLogs
from app.schemas import UserCreate, LoginRequest, TokenResponse
from app.helper.hash_helper import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, refresh_access_token, should_refresh_access_token
from app.security.access import admin_required, login_required, _redirect_to_login

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _is_secure_cookie() -> bool:
    return os.getenv("ENVIRONMENT", "DEV").upper() == "PROD"


def _access_cookie_max_age() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)) * 60


def _refresh_cookie_max_age() -> int:
    return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)) * 24 * 60 * 60

def _to_utc_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        # Treat stored naive values as UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _set_token_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=_is_secure_cookie(),
        samesite="lax",
        max_age=max_age,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
@login_required
@admin_required
def register(user: UserCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(Users).filter(
        (Users.username == user.username)
    ).first()
    
    if existing_user:
        AuthenticationLogs.track_register_user(db, user_id=str(existing_user.id), login_ip=get_ip_from_request(request), successful=False, event_notes="Username already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"  
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = Users.add_new_user(db=db, username=user.username, password_hash=hashed_password, is_admin=user.is_admin)
    AuthenticationLogs.track_register_user(db, user_id=str(db_user.id), login_ip=get_ip_from_request(request), successful=True, event_notes="User registered successfully")
    return db_user


@router.post("/login")
def login(response: Response, credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
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
        AuthenticationLogs.track_user_logging(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False, event_notes="Invalid password")
        return {
            "error": "Invalid username or password",
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    if not user.is_active:
        AuthenticationLogs.track_user_logging(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False, event_notes="User account is inactive")
        return {
            "error": "User account is inactive",
            "status_code": status.HTTP_403_FORBIDDEN
        }
    
    lockout_utc = _to_utc_aware(user.lockout_time)
    
    if lockout_utc and lockout_utc > datetime.now(timezone.utc):
        AuthenticationLogs.track_user_logging(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False, event_notes="User account is locked out")
        return {
            "error": f"Account locked until {lockout_utc.isoformat()}",
            "status_code": status.HTTP_403_FORBIDDEN
        }
    
    # Create access token
    token_payload = {"sub": user.username, "user_id": str(user.id), "is_admin": user.is_admin}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=True)
    AuthenticationLogs.track_user_logging(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=True, event_notes="User logged in successfully")

    _set_token_cookie(response, "access_token", access_token, _access_cookie_max_age())
    _set_token_cookie(response, "refresh_token", refresh_token, _refresh_cookie_max_age())
    
    return {"message": "Login successful"}


@router.post("/refresh")
def refresh_login_token(request: Request, response: Response):
    """Refresh the access token when the current one is nearly expired."""
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    current_access_token = request.cookies.get("access_token")
    if current_access_token and not should_refresh_access_token(current_access_token):
        return {"message": "Access token does not need refresh yet", "refreshed": False}

    refreshed_access_token = refresh_access_token(refresh_token_cookie, current_access_token)
    if not refreshed_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to refresh access token",
        )

    _set_token_cookie(response, "access_token", refreshed_access_token, _access_cookie_max_age())
    return {"message": "Access token refreshed", "refreshed": True}


@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request, db: Session = Depends(get_db)):
    """Logout user by clearing the access token cookie"""
    if request.state.user_id:
        AuthenticationLogs.track_user_logging(db=db, user_id=str(request.state.user_id), login_ip=get_ip_from_request(request), successful=True, event_notes="User logged out")
    redirect_response = _redirect_to_login(request, "Logged out successfully", "success")
    redirect_response.delete_cookie(key="access_token", path="/")
    redirect_response.delete_cookie(key="refresh_token", path="/")

    return redirect_response
