"""User models."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=12,
        description="Password (min 12 chars, must include uppercase, lowercase, numbers)",
    )


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class User(BaseModel):
    """User model (internal)."""

    id: int
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserResponse(BaseModel):
    """User response model (for API)."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: datetime = Field(..., description="Account creation time")

    class Config:
        """Pydantic config."""

        from_attributes = True
