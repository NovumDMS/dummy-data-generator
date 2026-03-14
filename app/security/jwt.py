"""JWT Token Handling"""
from datetime import datetime, timedelta, timezone
import os
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
import jwt

load_dotenv("working.env")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
ACCESS_TOKEN_REFRESH_THRESHOLD_SECONDS = 60
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def _normalize_jwt_payload(value):
    """Recursively convert non-JSON-safe payload values before JWT encoding."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _normalize_jwt_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_jwt_payload(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_normalize_jwt_payload(v) for v in value)
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_secret_key() -> str:
    return os.getenv("SECRET_KEY")


def _get_algorithm() -> str:
    return os.getenv("ALGORITHM", "HS256")


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    to_encode = _normalize_jwt_payload(data.copy())
    issued_at = _utc_now()
    expire = issued_at + expires_delta

    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "token_type": token_type,
    })

    return jwt.encode(
        to_encode,
        _get_secret_key(),
        algorithm=_get_algorithm(),
    )


def _strip_standard_claims(payload: dict) -> dict:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"exp", "iat", "nbf", "token_type"}
    }


def _decode_token(
    token: str,
    expected_token_type: Optional[str] = None,
    verify_exp: bool = True,
) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=[_get_algorithm()],
            options={"verify_exp": verify_exp},
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    if expected_token_type and payload.get("token_type") != expected_token_type:
        return None

    return payload


def _get_token_expiration(payload: dict) -> Optional[datetime]:
    exp = payload.get("exp")

    if isinstance(exp, datetime):
        if exp.tzinfo is None:
            return exp.replace(tzinfo=timezone.utc)
        return exp.astimezone(timezone.utc)

    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, tz=timezone.utc)

    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    token_expires_in = expires_delta or timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES))
    )
    return _create_token(data, ACCESS_TOKEN_TYPE, token_expires_in)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token."""
    token_expires_in = expires_delta or timedelta(
        days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS))
    )
    return _create_token(data, REFRESH_TOKEN_TYPE, token_expires_in)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token."""
    return _decode_token(token, expected_token_type=ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode JWT refresh token."""
    return _decode_token(token, expected_token_type=REFRESH_TOKEN_TYPE)


def get_token_time_remaining(token: str, expected_token_type: str = ACCESS_TOKEN_TYPE) -> Optional[timedelta]:
    """Return the remaining validity window for a signed token."""
    payload = _decode_token(token, expected_token_type=expected_token_type, verify_exp=False)
    if not payload:
        return None

    expiration = _get_token_expiration(payload)
    if not expiration:
        return None

    return expiration - _utc_now()


def should_refresh_access_token(
    token: str,
    threshold_seconds: int = ACCESS_TOKEN_REFRESH_THRESHOLD_SECONDS,
) -> bool:
    """Return True when the access token is at or below the refresh threshold."""
    time_remaining = get_token_time_remaining(token, expected_token_type=ACCESS_TOKEN_TYPE)
    if time_remaining is None:
        return False

    return time_remaining <= timedelta(seconds=threshold_seconds)


def refresh_access_token(
    refresh_token: str,
    current_access_token: Optional[str] = None,
    threshold_seconds: int = ACCESS_TOKEN_REFRESH_THRESHOLD_SECONDS,
) -> Optional[str]:
    """Create a new access token from a valid refresh token when refresh is needed."""
    refresh_payload = decode_refresh_token(refresh_token)
    if not refresh_payload:
        return None

    if current_access_token and not should_refresh_access_token(current_access_token, threshold_seconds):
        current_payload = decode_access_token(current_access_token)
        if current_payload:
            return None

    token_payload = _strip_standard_claims(refresh_payload)
    if not token_payload:
        return None

    return create_access_token(token_payload)
