"""
Authentication endpoints for the High School Management System API
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from ..authentication import create_session, get_current_teacher, revoke_session
from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": create_session(teacher["username"])
    }


@router.get("/check-session")
def check_session(
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Return the teacher associated with a valid session."""
    return teacher


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """Revoke the current teacher session."""
    revoke_session(authorization)
    return {"message": "Logged out"}
