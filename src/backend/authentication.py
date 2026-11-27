"""Authentication helpers for short-lived teacher sessions."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException

from .database import sessions_collection, teachers_collection

SESSION_DURATION = timedelta(days=7)


def _session_token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _session_id(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_session(username: str) -> str:
    """Create a session and return its opaque bearer token."""
    token = secrets.token_urlsafe(32)
    sessions_collection.insert_one({
        "_id": _session_id(token),
        "username": username,
        "expires_at": datetime.now(timezone.utc) + SESSION_DURATION
    })
    return token


def get_current_teacher(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Resolve and validate the teacher associated with a bearer session."""
    token = _session_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Teacher login required")

    session = sessions_collection.find_one({
        "_id": _session_id(token),
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    teacher = teachers_collection.find_one({"_id": session["username"]})
    if not teacher:
        raise HTTPException(status_code=401, detail="Teacher account not found")

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


def revoke_session(authorization: Optional[str]) -> None:
    """Revoke a bearer session if a token was supplied."""
    token = _session_token_from_header(authorization)
    if token:
        sessions_collection.delete_one({"_id": _session_id(token)})
