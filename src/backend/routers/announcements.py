"""Endpoints for public and teacher-managed announcements."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from ..authentication import get_current_teacher
from ..database import announcements_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementInput(BaseModel):
    """Fields shared by announcement creation and updates."""

    message: str = Field(..., min_length=1, max_length=500)
    start_date: Optional[date] = None
    expiration_date: date


def _validated_dates(announcement: AnnouncementInput) -> Dict[str, Any]:
    message = announcement.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Announcement message is required")
    if announcement.start_date and announcement.start_date > announcement.expiration_date:
        raise HTTPException(
            status_code=422,
            detail="Start date must be on or before the expiration date"
        )

    return {
        "message": message,
        "start_date": (
            announcement.start_date.isoformat()
            if announcement.start_date
            else None
        ),
        "expiration_date": announcement.expiration_date.isoformat()
    }


def _serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, str]:
    return {
        "id": str(announcement["_id"]),
        "message": announcement["message"],
        "start_date": announcement.get("start_date") or "",
        "expiration_date": announcement["expiration_date"]
    }


def _object_id(announcement_id: str) -> ObjectId:
    try:
        return ObjectId(announcement_id)
    except InvalidId as error:
        raise HTTPException(status_code=404, detail="Announcement not found") from error


@router.get("", response_model=List[Dict[str, str]])
def get_active_announcements() -> List[Dict[str, str]]:
    """Return announcements that are currently within their scheduled dates."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": {"$lte": today}}
        ]
    }
    announcements = announcements_collection.find(query).sort("expiration_date", 1)
    return [_serialize_announcement(item) for item in announcements]


@router.get(
    "/manage",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(get_current_teacher)]
)
def get_all_announcements() -> List[Dict[str, str]]:
    """List all announcements for a signed-in teacher."""
    announcements = announcements_collection.find().sort("expiration_date", 1)
    return [_serialize_announcement(item) for item in announcements]


@router.post(
    "",
    response_model=Dict[str, str],
    status_code=201,
    dependencies=[Depends(get_current_teacher)]
)
def create_announcement(
    announcement: AnnouncementInput
) -> Dict[str, str]:
    """Create an announcement for a signed-in teacher."""
    document = _validated_dates(announcement)
    result = announcements_collection.insert_one(document)
    return _serialize_announcement({
        "_id": result.inserted_id,
        **document
    })


@router.put(
    "/{announcement_id}",
    response_model=Dict[str, str],
    dependencies=[Depends(get_current_teacher)]
)
def update_announcement(
    announcement_id: str,
    announcement: AnnouncementInput
) -> Dict[str, str]:
    """Update an existing announcement for a signed-in teacher."""
    updated = announcements_collection.find_one_and_update(
        {"_id": _object_id(announcement_id)},
        {"$set": _validated_dates(announcement)},
        return_document=ReturnDocument.AFTER
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return _serialize_announcement(updated)


@router.delete(
    "/{announcement_id}",
    dependencies=[Depends(get_current_teacher)]
)
def delete_announcement(
    announcement_id: str
) -> Dict[str, str]:
    """Delete an existing announcement for a signed-in teacher."""
    result = announcements_collection.delete_one(
        {"_id": _object_id(announcement_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted"}
