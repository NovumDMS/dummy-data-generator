"""Authentication Routes"""
from datetime import datetime, timezone
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.helper.ip_helper import get_ip_from_request
from app.models.auth import Users
from app.schemas import UserCreate, LoginRequest, TokenResponse
from app.helper.hash_helper import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, refresh_access_token, should_refresh_access_token
from app.security.access import login_required, _redirect_to_login

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger(__name__)

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
def register(user: UserCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(Users).filter(
        (Users.username == user.username) | (Users.email == user.email)
    ).first()
    
    if existing_user:
        logger.warning(f"Registration attempt with existing username: {user.username} from IP: {get_ip_from_request(request)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"  
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = Users.add_new_user(db=db, username=user.username, password_hash=hashed_password, is_admin=user.is_admin, email=user.email)
    logger.info(f"User registered successfully: {user.username} from IP: {get_ip_from_request(request)}")
    return {"message": f"User {user.username} registered successfully"}
    db_user = Users.add_new_user(db=db, username=user.username, password_hash=hashed_password, is_admin=user.is_admin)
    logger.info(f"New user registered: {user.username} (Admin: {user.is_admin})")
    return db_user


@router.post("/login")
def login(response: Response, credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Find user
    user = db.query(Users).filter(Users.username == credentials.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user.username} from IP: {get_ip_from_request(request)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    lockout_utc = _to_utc_aware(user.lockout_time)
    
    if lockout_utc and lockout_utc > datetime.now(timezone.utc):
        logger.warning(f"Login attempt for locked out user: {user.username} from IP: {get_ip_from_request(request)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {lockout_utc.isoformat()}"
        )
    
    if not verify_password(credentials.password, user.password_hash):
        user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False)
        logger.warning(f"Invalid password attempt for user: {user.username} from IP: {get_ip_from_request(request)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

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
        logger.warning(f"Inactive user login attempt: {user.username} (ID: {user.id})")
        return {
            "error": "User account is inactive",
            "status_code": status.HTTP_404_NOT_FOUND
        }

    lockout_utc = _to_utc_aware(user.lockout_time)
    
    if lockout_utc and lockout_utc > datetime.now(timezone.utc):
        logger.warning(f"Locked out user login attempt: {user.username} (ID: {user.id})")
        return {
            "error": f"Account locked until {lockout_utc.isoformat()}",
            "status_code": status.HTTP_404_NOT_FOUND
        }
    
    if not verify_password(credentials.password, user.password_hash):
        user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=False)
        logger.warning(f"Invalid password attempt for user: {user.username} (ID: {user.id})")
        return {
            "error": "Invalid username or password",
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    # Create access token
    token_payload = {"sub": user.username, "user_id": str(user.id), "is_admin": user.is_admin}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    user.track_user_login(db, user_id=user.id, login_ip=get_ip_from_request(request), successful=True)
    logger.info(f"User logged in successfully: {user.username} from IP: {get_ip_from_request(request)}")

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

    logger.info("Access token refreshed successfully")
    _set_token_cookie(response, "access_token", refreshed_access_token, _access_cookie_max_age())
    return {"message": "Access token refreshed", "refreshed": True}


@router.api_route("/logout", methods=["GET", "POST"])
def logout(request: Request):
    """Logout user by clearing the access token cookie"""
    redirect_response = _redirect_to_login(request, "Logged out successfully", "success")
    redirect_response.delete_cookie(key="access_token", path="/")
    redirect_response.delete_cookie(key="refresh_token", path="/")
    logger.info("User logged out successfully")

    return redirect_response
