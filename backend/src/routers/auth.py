"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models import UserCreate, UserResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request."""

    email: str
    password: str


# In-memory user storage for demo (Task #11 will use database)
users_db: dict[int, dict] = {}
next_user_id = 1


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(req: UserCreate) -> UserResponse:
    """Register a new user.

    Args:
        req: UserCreate with email and password

    Returns:
        Created user details (no password)

    Raises:
        400: Invalid email or password
        409: Email already registered
    """
    global next_user_id

    # Check email not already registered
    for user in users_db.values():
        if user["email"] == req.email:
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            )

    user_id = next_user_id
    next_user_id += 1

    user = {
        "id": user_id,
        "email": req.email,
        "password_hash": AuthService.hash_password(req.password),
        "created_at": "2024-07-29T00:00:00",
    }

    users_db[user_id] = user

    return UserResponse(
        id=user["id"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/login", response_model=Token)
async def login(req: LoginRequest) -> Token:
    """Login and get JWT token.

    Args:
        req: LoginRequest with email and password

    Returns:
        JWT access token

    Raises:
        401: Invalid email or password
    """
    # Find user
    user = None
    for u in users_db.values():
        if u["email"] == req.email:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Verify password
    if not AuthService.verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Create token
    token = AuthService.create_access_token(user["id"])

    return Token(access_token=token, token_type="bearer")


@router.post("/logout")
async def logout() -> dict:
    """Logout endpoint (tokens are stateless, this is a client-side operation).

    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}
