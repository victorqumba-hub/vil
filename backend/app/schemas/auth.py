"""Pydantic schemas for authentication & broker integration."""

import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


# ── Password Validation ─────────────────────────────────────────────────────

def validate_password_strength(password: str) -> str:
    """Enforce institutional-grade password policy."""
    errors = []
    if len(password) < 12:
        errors.append("at least 12 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("one digit")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", password):
        errors.append("one special character")
    if errors:
        raise ValueError(f"Password must contain: {', '.join(errors)}")
    return password


# ── Auth Schemas ─────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    display_name: str | None = None
    phone: str | None = None
    country: str | None = None
    account_type: str = Field(default="demo", pattern="^(demo|live)$")
    accept_terms: bool = Field(default=False)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_password_strength(v)

    @field_validator("accept_terms")
    @classmethod
    def must_accept(cls, v):
        if not v:
            raise ValueError("You must accept the Terms & Risk Disclosure")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 1800  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v):
        return validate_password_strength(v)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    display_name: str | None
    role: str
    account_type: str
    is_verified: bool
    is_active: bool
    country: str | None
    phone: str | None
    broker_connected: bool = False
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


# ── Broker Integration Schemas ───────────────────────────────────────────────


class BrokerConnectRequest(BaseModel):
    account_id: str = Field(min_length=3, max_length=100)
    api_key: str = Field(min_length=10, max_length=500)
    environment: str = Field(default="practice", pattern="^(practice|live)$")


class BrokerAccountResponse(BaseModel):
    id: str
    broker_name: str
    account_id: str
    environment: str
    is_active: bool
    account_currency: str | None
    cached_balance: float | None
    cached_equity: float | None
    cached_margin_used: float | None
    cached_open_trade_count: int | None
    last_synced_at: datetime | None
    api_key_masked: str  # Last 4 chars only

    model_config = {
        "from_attributes": True
    }


class BrokerStatusResponse(BaseModel):
    connected: bool
    broker: BrokerAccountResponse | None = None
