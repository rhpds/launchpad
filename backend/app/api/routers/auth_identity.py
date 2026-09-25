from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.oauth import User, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthenticatedIdentity(BaseModel):
    username: str
    email: str | None = None
    is_admin: bool
    identity_verified: bool


@router.get("/me", response_model=AuthenticatedIdentity)
def current_identity(user: User = Depends(get_current_user)) -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        identity_verified=user.identity_verified,
    )
