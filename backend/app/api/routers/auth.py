"""
Auth router — /api/v1/auth

POST  /api/v1/auth/register   Create a new user account
POST  /api/v1/auth/login      Obtain a JWT access token
GET   /api/v1/auth/me         Return the current authenticated user
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator

from app.core.security import create_access_token, hash_password, verify_password, decode_access_token
from app.db.models import UserDoc
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Username must be at least 2 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool


# ---------------------------------------------------------------------------
# Dependency — current user from Bearer token
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserDoc:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await UserDoc.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterRequest) -> TokenOut:
    if await UserDoc.find_one(UserDoc.email == body.email.lower()):
        raise HTTPException(status_code=409, detail="Email already registered")
    if await UserDoc.find_one(UserDoc.username == body.username.lower()):
        raise HTTPException(status_code=409, detail="Username already taken")

    user = UserDoc(
        email=body.email.lower(),
        username=body.username.lower(),
        hashed_password=hash_password(body.password),
    )
    await user.insert()

    token = create_access_token(str(user.id))
    logger.info("New user registered: %s (%s)", user.username, user.email)
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginRequest) -> TokenOut:
    user = await UserDoc.find_one(UserDoc.email == body.email.lower())
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(str(user.id))
    logger.info("User logged in: %s", user.email)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: UserDoc = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
    )
