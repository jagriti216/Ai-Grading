"""
Admin routes — creating and listing teacher/student accounts.
Admin-only: gated by require_role("admin") on every route here.
"""

import uuid
import secrets
import string
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from stage5_api.db.mongo import users
from stage5_api.auth import hash_password, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str
    name: str
    role: str  # "teacher" or "student"
    initial_password: Optional[str] = None  # if omitted, a random one is generated
    roll_no: Optional[str] = None
    class_name: Optional[str] = None
    subject_codes: Optional[List[str]] = None  # subjects this teacher teaches


def _generate_temp_password(length: int = 10) -> str:
    # avoid visually-ambiguous characters (0/O, l/1) since this gets read off a screen and typed by hand
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.post("/users")
async def create_user(body: CreateUserRequest, _: dict = Depends(require_role("admin"))):
    if body.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="role must be 'teacher' or 'student'")

    if users().find_one({"username": body.username}):
        raise HTTPException(status_code=409, detail=f"Username '{body.username}' already exists")

    if body.role == "student" and not body.roll_no:
        raise HTTPException(status_code=400, detail="roll_no is required for student accounts")

    temp_password = body.initial_password or _generate_temp_password()

    user_doc = {
        "user_id": str(uuid.uuid4()),
        "username": body.username,
        "name": body.name,
        "role": body.role,
        "password_hash": hash_password(temp_password),
        "must_change_password": True,
        "roll_no": body.roll_no if body.role == "student" else None,
        "class_name": body.class_name,
        "subject_codes": body.subject_codes if body.role == "teacher" else None,
        "created_at": datetime.utcnow().isoformat(),
    }
    users().insert_one(user_doc)

    return {
        "user_id": user_doc["user_id"],
        "username": user_doc["username"],
        "name": user_doc["name"],
        "role": user_doc["role"],
        "temporary_password": temp_password,
        "message": "Account created. Share this temporary password securely (it is shown only once) — "
                    "the user must change it on first login.",
    }


@router.get("/users")
async def list_users(role: Optional[str] = None, _: dict = Depends(require_role("admin"))):
    all_users = users().find({"role": role}) if role else users().find({})
    return [
        {
            "user_id": u["user_id"],
            "username": u["username"],
            "name": u["name"],
            "role": u["role"],
            "roll_no": u.get("roll_no"),
            "class_name": u.get("class_name"),
            "subject_codes": u.get("subject_codes"),
            "created_at": u.get("created_at"),
        }
        for u in all_users
        if u["role"] != "admin"
    ]


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, _: dict = Depends(require_role("admin"))):
    target = users().find_one({"user_id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["role"] == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete an admin account")
    users().delete_one({"user_id": user_id})
    return {"message": "User deleted"}
