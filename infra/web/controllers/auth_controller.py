import secrets
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from core.security.password_utils import hash_password, verify_password
from infra.db.user_repository_impl import PostgreSQLUserRepository
from core.entities.user import User as UserEntity

router = APIRouter()
security = HTTPBasic()
repo = PostgreSQLUserRepository()

class SetPasswordRequest(BaseModel):
    """Request model for changing user password, requires old and new passwords."""
    user_id: int = Field(..., description="Internal user ID")
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password to set")

class APIKeyResponse(BaseModel):
    """Response model for API key generation."""
    api_key: str = Field(..., description="Generated API key for prediction endpoint")

@router.post("/auth/set-password")
async def set_password(request: SetPasswordRequest):
    """Changes the password for a user after verifying the old password."""
    user = repo.get_by_id(request.user_id)
    if not user:
        logging.warning(f"User not found for setting password: {request.user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    # verify old password
    if not user.password_hash or not verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    pwd_hash = hash_password(request.new_password)
    success = repo.update_password_hash(user.id, pwd_hash)
    if not success:
        logging.error(f"Failed to update password for user ID: {user.id}")
        raise HTTPException(status_code=500, detail="Failed to set password")
    return {"message": "Password set successfully"}

@router.post("/auth/apikey", response_model=APIKeyResponse)
async def generate_api_key(
    credentials: HTTPBasicCredentials = Depends(security)
):
    """Generates and returns a new API key for authenticated user."""
    # Expect username to be internal user ID
    try:
        user_id = int(credentials.username)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    password = credentials.password
    user = repo.get_by_id(user_id)
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # generate new API key
    api_key = secrets.token_hex(32)
    success = repo.update_api_key(user.id, api_key)
    if not success:
        logging.error(f"Failed to update api_key for user ID: {user.id}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")
    return {"api_key": api_key}
