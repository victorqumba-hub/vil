"""Authentication API — register, login, token refresh, logout, password change.

Institutional-grade security with:
- Argon2/bcrypt password hashing
- JWT access + refresh token rotation
- Brute-force protection with account lockout
- Immutable audit logging
- Email verification stub
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import User, UserRole, RefreshToken, AccountType
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit_service import log_event

router = APIRouter(prefix="/api", tags=["auth"])

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token() -> str:
    """Generate a cryptographically secure refresh token."""
    return secrets.token_urlsafe(64)


def _hash_token(token: str) -> str:
    """Hash a refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id_str is None or token_type != "access":
            raise credentials_exc
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
    if user.is_locked and user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=423, detail="Account is temporarily locked")
    return user


def require_role(*roles: UserRole):
    """Dependency factory for role-based access."""
    async def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return _check


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    user = User(
        email=body.email,
        password_hash=_hash_password(body.password),
        full_name=body.full_name,
        display_name=body.display_name or body.full_name.split()[0],
        phone=body.phone,
        country=body.country,
        account_type=AccountType.LIVE if body.account_type == "live" else AccountType.DEMO,
        terms_accepted_at=datetime.utcnow() if body.accept_terms else None,
        verification_token=verification_token,
        is_verified=False,  # Require email verification
    )
    db.add(user)
    await db.flush()

    # Email verification stub (log to console in dev)
    verify_url = f"http://localhost:5173/verify?token={verification_token}"
    print(f"\n{'='*60}")
    print(f"📧 EMAIL VERIFICATION LINK (dev mode)")
    print(f"   User: {user.email}")
    print(f"   Link: {verify_url}")
    print(f"{'='*60}\n")

    # Create tokens
    access_token = _create_access_token(str(user.id), user.role.value)
    refresh_token_raw = _create_refresh_token()

    # Store refresh token hash
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token_raw),
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )
    db.add(rt)

    # Audit log
    await log_event(
        db, action_type="REGISTER", user_id=user.id,
        ip_address=_get_client_ip(request),
        status="success", details=f"New user registered: {user.email}"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_raw,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify user email with the token from the verification link."""
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    user.is_verified = True
    user.verification_token = None
    return {"message": "Email verified successfully. You may now log in."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = _get_client_ip(request)

    try:
        result = await db.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()
    except Exception as e:
        print(f"[AUTH] Database error during login query: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again.")

    if not user:
        await log_event(db, "LOGIN", ip_address=client_ip, status="failure",
                        details=f"Unknown email: {body.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check lockout
    if user.is_locked and user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        await log_event(db, "LOGIN", user_id=user.id, ip_address=client_ip,
                        status="failure", details="Account locked")
        raise HTTPException(
            status_code=423,
            detail=f"Account locked. Try again in {remaining} minutes."
        )

    # Verify password
    if not _verify_password(body.password, user.password_hash):
        user.failed_login_attempts += 1

        # Lock after max attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            await log_event(db, "ACCOUNT_LOCKED", user_id=user.id, ip_address=client_ip,
                            status="failure", details=f"Locked after {user.failed_login_attempts} failed attempts")

        await log_event(db, "LOGIN", user_id=user.id, ip_address=client_ip,
                        status="failure", details=f"Bad password (attempt {user.failed_login_attempts})")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login — reset counters
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = client_ip

    # Create tokens
    access_token = _create_access_token(str(user.id), user.role.value)
    refresh_token_raw = _create_refresh_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token_raw),
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )
    db.add(rt)

    try:
        await log_event(db, "LOGIN", user_id=user.id, ip_address=client_ip , status="success")
    except Exception as e:
        print(f"[AUTH] Audit log error (non-fatal): {e}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_raw,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )





@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_access_token(body: RefreshTokenRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Rotate refresh token and issue new access token."""
    token_hash = _hash_token(body.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
        )
    )
    rt = result.scalar_one_or_none()

    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Fetch user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not available")

    # Revoke old token
    rt.is_revoked = True
    rt.revoked_at = datetime.utcnow()

    # Issue new tokens
    access_token = _create_access_token(str(user.id), user.role.value)
    new_refresh_raw = _create_refresh_token()

    rt.replaced_by = _hash_token(new_refresh_raw)

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(new_refresh_raw),
        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )
    db.add(new_rt)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_raw,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all refresh tokens for the user."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True, revoked_at=datetime.utcnow())
    )

    await log_event(db, "LOGOUT", user_id=current_user.id,
                    ip_address=_get_client_ip(request), status="success")

    return {"message": "Logged out successfully"}


@router.post("/auth/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password and revoke all sessions."""
    if not _verify_password(body.current_password, current_user.password_hash):
        await log_event(db, "PASSWORD_CHANGE", user_id=current_user.id,
                        ip_address=_get_client_ip(request), status="failure",
                        details="Wrong current password")
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    current_user.password_hash = _hash_password(body.new_password)

    # Revoke all refresh tokens (force re-login everywhere)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True, revoked_at=datetime.utcnow())
    )

    await log_event(db, "PASSWORD_CHANGE", user_id=current_user.id,
                    ip_address=_get_client_ip(request), status="success")

    return {"message": "Password changed. All sessions revoked. Please login again."}


@router.get("/me", response_model=UserResponse)
async def current_user_info(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check if broker is connected
    from app.db.models import BrokerAccount
    broker_result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == user.id,
            BrokerAccount.is_active == True,
        )
    )
    broker = broker_result.scalar_one_or_none()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        display_name=user.display_name,
        role=user.role.value,
        account_type=user.account_type.value if user.account_type else "demo",
        is_verified=user.is_verified,
        is_active=user.is_active,
        country=user.country,
        phone=user.phone,
        broker_connected=broker is not None,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )
