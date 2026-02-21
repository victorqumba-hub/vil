"""Broker Integration API — Connect, status, disconnect, sync OANDA accounts.

Handles per-user encrypted credential storage and OANDA account validation.
All credentials are encrypted at rest using AES-256-GCM.
"""

import httpx
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import BrokerAccount, BrokerEnvironment, User
from app.api.auth import get_current_user, _get_client_ip
from app.services.credential_vault import encrypt_credential, decrypt_credential, mask_api_key
from app.services.audit_service import log_event
from app.schemas.auth import BrokerConnectRequest, BrokerAccountResponse, BrokerStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/broker-integration", tags=["Broker Integration"])


def _oanda_base_url(environment: str) -> str:
    """Return the correct OANDA API base URL."""
    if environment == "live":
        return "https://api-fxtrade.oanda.com/v3"
    return "https://api-fxpractice.oanda.com/v3"


async def _test_oanda_connection(account_id: str, api_key: str, environment: str) -> dict:
    """Test OANDA credentials by fetching account summary."""
    base_url = _oanda_base_url(environment)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{base_url}/accounts/{account_id}/summary",
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            account = data.get("account", {})
            return {
                "success": True,
                "balance": float(account.get("balance", 0)),
                "equity": float(account.get("NAV", 0)),
                "margin_used": float(account.get("marginUsed", 0)),
                "open_trade_count": int(account.get("openTradeCount", 0)),
                "currency": account.get("currency", "USD"),
            }
        except httpx.HTTPStatusError as e:
            logger.warning(f"OANDA validation failed: {e.response.status_code}")
            return {"success": False, "error": f"OANDA rejected credentials: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"OANDA connection error: {e}")
            return {"success": False, "error": str(e)}


def _broker_to_response(ba: BrokerAccount, decrypted_key: str = "") -> BrokerAccountResponse:
    """Convert a BrokerAccount model to API response."""
    return BrokerAccountResponse(
        id=str(ba.id),
        broker_name=ba.broker_name,
        account_id=ba.account_id,
        environment=ba.environment.value,
        is_active=ba.is_active,
        account_currency=ba.account_currency,
        cached_balance=ba.cached_balance,
        cached_equity=ba.cached_equity,
        cached_margin_used=ba.cached_margin_used,
        cached_open_trade_count=ba.cached_open_trade_count,
        last_synced_at=ba.last_synced_at,
        api_key_masked=mask_api_key(decrypted_key) if decrypted_key else "****",
    )


@router.post("/connect", response_model=BrokerAccountResponse, status_code=201)
async def connect_broker(
    body: BrokerConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a user's OANDA account with encrypted credentials."""

    # Check if user already has an active broker
    existing = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Broker already connected. Disconnect first.")

    # Test the credentials against OANDA
    test_result = await _test_oanda_connection(body.account_id, body.api_key, body.environment)
    if not test_result.get("success"):
        await log_event(
            db, "BROKER_CONNECT", user_id=current_user.id,
            ip_address=_get_client_ip(request), status="failure",
            details=f"OANDA validation failed: {test_result.get('error')}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Could not connect to OANDA: {test_result.get('error')}"
        )

    # Encrypt the API key
    ciphertext, iv, tag = encrypt_credential(body.api_key)

    env = BrokerEnvironment.LIVE if body.environment == "live" else BrokerEnvironment.PRACTICE

    broker_account = BrokerAccount(
        user_id=current_user.id,
        broker_name="oanda",
        account_id=body.account_id,
        encrypted_api_key=ciphertext,
        encryption_iv=iv,
        encryption_tag=tag,
        environment=env,
        is_active=True,
        account_currency=test_result.get("currency", "USD"),
        cached_balance=test_result.get("balance"),
        cached_equity=test_result.get("equity"),
        cached_margin_used=test_result.get("margin_used"),
        cached_open_trade_count=test_result.get("open_trade_count"),
        last_synced_at=datetime.utcnow(),
    )
    db.add(broker_account)
    await db.flush()

    await log_event(
        db, "BROKER_CONNECT", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Connected OANDA account {body.account_id} ({body.environment})"
    )

    return _broker_to_response(broker_account, body.api_key)


@router.get("/status", response_model=BrokerStatusResponse)
async def broker_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if the current user has a linked broker account."""
    result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.is_active == True,
        )
    )
    ba = result.scalar_one_or_none()

    if not ba:
        return BrokerStatusResponse(connected=False)

    # Decrypt key for masked display
    try:
        decrypted = decrypt_credential(ba.encrypted_api_key, ba.encryption_iv, ba.encryption_tag)
    except Exception:
        decrypted = ""

    return BrokerStatusResponse(
        connected=True,
        broker=_broker_to_response(ba, decrypted),
    )


@router.delete("/disconnect")
async def disconnect_broker(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the user's broker account."""
    result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.is_active == True,
        )
    )
    ba = result.scalar_one_or_none()
    if not ba:
        raise HTTPException(status_code=404, detail="No active broker connection")

    ba.is_active = False

    await log_event(
        db, "BROKER_DISCONNECT", user_id=current_user.id,
        ip_address=_get_client_ip(request), status="success",
        details=f"Disconnected OANDA account {ba.account_id}"
    )

    return {"message": "Broker disconnected successfully"}


@router.post("/sync")
async def sync_broker_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync latest account data from OANDA."""
    result = await db.execute(
        select(BrokerAccount).where(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.is_active == True,
        )
    )
    ba = result.scalar_one_or_none()
    if not ba:
        raise HTTPException(status_code=404, detail="No active broker connection")

    # Decrypt credentials
    api_key = decrypt_credential(ba.encrypted_api_key, ba.encryption_iv, ba.encryption_tag)
    env = ba.environment.value

    sync_result = await _test_oanda_connection(ba.account_id, api_key, env)
    if not sync_result.get("success"):
        raise HTTPException(status_code=502, detail="Failed to sync with OANDA")

    ba.cached_balance = sync_result.get("balance")
    ba.cached_equity = sync_result.get("equity")
    ba.cached_margin_used = sync_result.get("margin_used")
    ba.cached_open_trade_count = sync_result.get("open_trade_count")
    ba.last_synced_at = datetime.utcnow()

    return {
        "message": "Synced successfully",
        "balance": ba.cached_balance,
        "equity": ba.cached_equity,
        "margin_used": ba.cached_margin_used,
        "open_trades": ba.cached_open_trade_count,
    }
