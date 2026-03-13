from datetime import datetime, timezone
from functools import wraps
import inspect
from urllib.parse import urlencode
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app.security.jwt import decode_access_token


def _redirect_to_login(request: Request, message: str, level: str = "warning"):
    request.session["flash"] = {
        "message": message,
        "level": level
    }
    return RedirectResponse("/login", status_code=303)

def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from kwargs (FastAPI passes it)
        request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request context not found"
            )
        
        # Check for JWT cookie
        token = request.cookies.get("access_token")
        
        if not token:
            return _redirect_to_login(request, "Please log in to continue", "info")
        
        # Validate the token
        payload = decode_access_token(token)
        print(f"Decoded JWT payload: {payload}")  # Debugging statement
        print(f"Current Time: {datetime.now(timezone.utc)}")  # Debugging statement
        
        if not payload:
            return _redirect_to_login(request, "Session expired. Please log in again", "warning")
        
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
    
    return wrapper

def admin_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from kwargs (FastAPI passes it)
        request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request context not found"
            )
        
        # Check for JWT cookie
        token = request.cookies.get("access_token")
        
        if not token:
            return _redirect_to_login(request, "Please log in to continue", "info")
        
        # Validate the token
        payload = decode_access_token(token)
        
        if not payload:
            return _redirect_to_login(request, "Session expired. Please log in again", "warning")

        if not payload.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
    
    return wrapper
