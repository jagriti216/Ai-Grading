"""
Auth routes — login, current-user info, self-service password change.
Account creation itself is admin-only (see routes/admin.py) — nobody
signs themselves up, since roll numbers / teacher assignments need to
be set up deliberately by an admin.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from stage5_api.db.mongo import users
from stage5_api.auth import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
async def login(body: LoginRequest):
    user = users().find_one({"username": body.username})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user_id=user["user_id"], role=user["role"], name=user["name"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "username": user["username"],
        "name": user["name"],
        "role": user["role"],
        "must_change_password": user.get("must_change_password", False),
        "roll_no": user.get("roll_no"),
        "subject_codes": user.get("subject_codes"),
    }


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    user = users().find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "name": user["name"],
        "role": user["role"],
        "roll_no": user.get("roll_no"),
        "class_name": user.get("class_name"),
        "subject_codes": user.get("subject_codes"),
        "must_change_password": user.get("must_change_password", False),
    }


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user = users().find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    if verify_password(body.new_password, user["password_hash"]):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from your current (temporary) password",
        )

    users().update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"password_hash": hash_password(body.new_password), "must_change_password": False}},
    )
    return {"message": "Password updated successfully"}
