"""Audit Service — Immutable event logging for VIL.

Logs all security-sensitive actions (login, logout, broker integration,
trade execution, password changes, admin actions) to an immutable audit table.
"""

import hashlib
import json
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog

logger = logging.getLogger(__name__)


async def log_event(
    db: AsyncSession,
    action_type: str,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
    details: str | None = None,
    payload: dict | None = None,
) -> None:
    """
    Log an immutable audit event.
    
    Args:
        db: Database session
        action_type: One of LOGIN, LOGOUT, REGISTER, BROKER_CONNECT,
                     BROKER_DISCONNECT, TRADE_EXECUTE, PASSWORD_CHANGE,
                     ROLE_CHANGE, ADMIN_SUSPEND, ADMIN_FORCE_LOGOUT, etc.
        user_id: The user performing the action
        ip_address: Client IP address
        user_agent: Client user agent string
        status: "success" or "failure"
        details: Human-readable description
        payload: Optional dict to hash for integrity verification
    """
    payload_hash = None
    if payload:
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        ip_address=ip_address,
        user_agent=user_agent,
        payload_hash=payload_hash,
        status=status,
        details=details,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    # Don't flush here — let the session commit handle it
    logger.info(f"AUDIT [{action_type}] user={user_id} status={status} ip={ip_address}")
