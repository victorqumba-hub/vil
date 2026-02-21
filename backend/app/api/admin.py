"""Admin Control Panel API — User oversight, system monitoring, governance.

Restricted to ADMIN and SUPER_ADMIN roles only.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import (
    AuditLog, BrokerAccount, RefreshToken, Signal, Trade, User, UserRole,
)
from app.api.auth import get_current_user, require_role, _get_client_ip
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# All routes require ADMIN or SUPER_ADMIN
admin_dep = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)


@router.get("/users")
async def list_users(
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """List all users with status and stats."""
    result = await db.execute(select(User))
    users = result.scalars().all()

    user_list = []
    for u in users:
        # Count broker connections
        broker_result = await db.execute(
            select(func.count(BrokerAccount.id)).where(
                BrokerAccount.user_id == u.id,
                BrokerAccount.is_active == True,
            )
        )
        broker_count = broker_result.scalar() or 0

        # Count trades
        trade_result = await db.execute(
            select(func.count(Trade.id)).where(Trade.user_id == u.id)
        )
        trade_count = trade_result.scalar() or 0

        user_list.append({
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "is_locked": u.is_locked,
            "broker_linked": broker_count > 0,
            "trade_count": trade_count,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {"users": user_list, "total": len(user_list)}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Cannot suspend admin accounts")

    target.is_active = False

    await log_event(
        db, "ADMIN_SUSPEND", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Suspended user {target.email}"
    )

    return {"message": f"User {target.email} suspended"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a suspended user."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.is_active = True
    target.is_locked = False
    target.locked_until = None
    target.failed_login_attempts = 0

    await log_event(
        db, "ADMIN_ACTIVATE", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Activated user {target.email}"
    )

    return {"message": f"User {target.email} activated"}


@router.post("/users/{user_id}/force-logout")
async def force_logout(
    user_id: str,
    request: Request,
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all sessions for a user."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        .values(is_revoked=True, revoked_at=datetime.utcnow())
    )

    await log_event(
        db, "ADMIN_FORCE_LOGOUT", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Force-logged out user {user_id}"
    )

    return {"message": "All sessions revoked"}


@router.post("/users/{user_id}/disable-broker")
async def disable_broker(
    user_id: str,
    request: Request,
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Disable a user's broker integration."""
    result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == user_id,
            BrokerAccount.is_active == True,
        )
    )
    ba = result.scalar_one_or_none()
    if not ba:
        raise HTTPException(status_code=404, detail="No active broker for this user")

    ba.is_active = False

    await log_event(
        db, "ADMIN_DISABLE_BROKER", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Disabled broker for user {user_id}"
    )

    return {"message": "Broker integration disabled"}


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    action_type: str | None = None,
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """View immutable audit logs."""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action_type": log.action_type,
                "ip_address": log.ip_address,
                "status": log.status,
                "details": log.details,
                "payload_hash": log.payload_hash,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/system-health")
async def system_health(
    current_user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """System health overview for admin dashboard."""
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0
    broker_count = (await db.execute(
        select(func.count(BrokerAccount.id)).where(BrokerAccount.is_active == True)
    )).scalar() or 0
    signal_count = (await db.execute(select(func.count(Signal.id)))).scalar() or 0
    trade_count = (await db.execute(select(func.count(Trade.id)))).scalar() or 0

    return {
        "users": {"total": user_count, "active": active_users},
        "brokers": {"connected": broker_count},
        "signals": {"total": signal_count},
        "trades": {"total": trade_count},
        "system": {
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG,
            "ml_service": settings.ML_SERVICE_URL,
        }
    }
