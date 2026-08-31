from functools import wraps
import inspect
import os
from types import SimpleNamespace

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.security.jwt import decode_access_token, refresh_access_token, should_refresh_access_token


def _redirect_to_login(request: Request, message: str, level: str = "warning"):
    request.session["flash"] = {
        "message": message,
        "level": level,
    }
    return RedirectResponse("/login", status_code=303)


def _access_cookie_max_age() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)) * 60


def _is_secure_cookie() -> bool:
    return os.getenv("ENVIRONMENT", "DEV").upper() == "PROD"


def _extract_request(args, kwargs) -> Request | None:
    request = kwargs.get("request")
    if request:
        return request

    for arg in args:
        if isinstance(arg, Request):
            return arg

    return None


def _extract_response(args, kwargs) -> Response | None:
    response = kwargs.get("response")
    if response:
        return response

    for arg in args:
        if isinstance(arg, Response):
            return arg

    return None


def _set_access_token_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_is_secure_cookie(),
        samesite="lax",
        max_age=_access_cookie_max_age(),
        path="/",
    )


def _store_user_context(request: Request, payload: dict) -> None:
    request.state.jwt_payload = payload
    request.state.user = SimpleNamespace(
        id=payload.get("user_id"),
        username=payload.get("sub"),
        is_admin=payload.get("is_admin", False),
    )


def _get_authenticated_payload(request: Request) -> tuple[dict | None, str | None]:
    cached_payload = getattr(request.state, "jwt_payload", None)
    cached_access_token = getattr(request.state, "refreshed_access_token", None)
    if cached_payload:
        return cached_payload, cached_access_token

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    refreshed_access_token = None

    payload = decode_access_token(access_token) if access_token else None

    if payload and access_token and should_refresh_access_token(access_token) and refresh_token:
        refreshed_access_token = refresh_access_token(refresh_token, access_token)
        if refreshed_access_token:
            payload = decode_access_token(refreshed_access_token) or payload

    if not payload and refresh_token:
        refreshed_access_token = refresh_access_token(refresh_token, access_token)
        if refreshed_access_token:
            payload = decode_access_token(refreshed_access_token)

    if payload:
        request.state.refreshed_access_token = refreshed_access_token
        _store_user_context(request, payload)
        return payload, refreshed_access_token

    return None, None


def _attach_refreshed_access_cookie(result, response: Response | None, refreshed_access_token: str | None) -> None:
    if not refreshed_access_token:
        return

    if isinstance(result, Response):
        _set_access_token_cookie(result, refreshed_access_token)
        return

    if response is not None:
        _set_access_token_cookie(response, refreshed_access_token)


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = _extract_request(args, kwargs)
        response = _extract_response(args, kwargs)

        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request context not found",
            )

        if not request.cookies.get("access_token") and not request.cookies.get("refresh_token"):
            return _redirect_to_login(request, "Please log in to continue", "info")

        payload, refreshed_access_token = _get_authenticated_payload(request)

        if not payload:
            return _redirect_to_login(request, "Session expired. Please log in again", "warning")

        if not payload.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )

        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result

        _attach_refreshed_access_cookie(result, response, refreshed_access_token)
        return result

    return wrapper
