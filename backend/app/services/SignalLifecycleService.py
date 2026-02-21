"""Signal Lifecycle Service — High-frequency governance and state management."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Signal, Asset, LifecycleStatus, SignalAuditEvent, MarketRegime
from app.services.data_ingestion import get_data_provider
from app.services.regime_classifier import classify_regime, Regime
from app.services.signal_scorer import score_signal
from app.ws.websocket import manager as ws_manager
from app.services.asset_manager import AssetManager
from app.services.ForensicService import forensic_service

logger = logging.getLogger(__name__)

class SignalLifecycleService:
    def __init__(self):
        self.evaluation_interval = 15  # seconds
        self.min_score_threshold = 40.0
        self.regime_strength_threshold = 0.5 # Example threshold

    async def run_cycle(self, db: AsyncSession):
        """Perform one evaluation cycle for all non-terminal signals."""
        logger.info("[LifecycleService] Starting evaluation cycle...")
        
        # 1. Fetch PENDING and ACTIVE signals
        query = (
            select(Signal)
            .options(selectinload(Signal.asset))
            .where(Signal.status.in_([
                LifecycleStatus.PENDING, 
                LifecycleStatus.ACTIVE,
                LifecycleStatus.QUEUED,
                LifecycleStatus.VALIDATED
            ]))
        )
        result = await db.execute(query)
        signals = result.scalars().all()
        
        if not signals:
            logger.info("[LifecycleService] No active signals to evaluate.")
            return

        provider = get_data_provider("oanda")
        
        for signal in signals:
            try:
                await self._evaluate_signal(signal, db, provider)
            except Exception as e:
                logger.error(f"[LifecycleService] Error evaluating signal {signal.id}: {e}")
        
        await db.commit()

    async def _evaluate_signal(self, signal: Signal, db: AsyncSession, provider: Any):
        now = datetime.utcnow()
        symbol = signal.asset.symbol
        old_status = signal.status
        new_status = old_status
        reason = ""

        # A. Time-Based TTL Check
        if signal.valid_until and now > signal.valid_until:
            if signal.status != LifecycleStatus.ACTIVE:
                new_status = LifecycleStatus.EXPIRED
                reason = f"TTL Expired (validUntil: {signal.valid_until})"

        # B. Technical Re-validation (Regime & Score)
        if new_status == old_status and signal.status == LifecycleStatus.PENDING:
            # Fetch fresh context
            # (Note: In production, we'd cache this across signals for the same asset)
            candles = await provider.fetch_ohlcv(symbol, "H1", 50)
            tick = await provider.fetch_tick(symbol)
            price = (tick["bid"] + tick["ask"]) / 2
            
            # Simplified regime check (placeholder for full logic)
            # regime_data = classify_regime(...) 
            # If currentRegime != signal.regime ...
            
            # C. Score Decay Check
            # (Placeholder: In a full implementation, we'd re-compute the score here)
            # If current_score < threshold -> LifecycleStatus.EXPIRED_SCORE_DECAY
            
            pass

        # Update if changed
        if new_status != old_status:
            logger.info(f"[LifecycleService] Transitioning {symbol} ({signal.id}) from {old_status} to {new_status}: {reason}")
            signal.status = new_status
            
            # terminal_statuses = [SUCCESS, FAILED, DROPPED, SUPPRESSED, EXPIRED, CANCELLED]
            is_terminal = new_status in [
                LifecycleStatus.SUCCESS, 
                LifecycleStatus.FAILED, 
                LifecycleStatus.DROPPED, 
                LifecycleStatus.SUPPRESSED, 
                LifecycleStatus.EXPIRED, 
                LifecycleStatus.CANCELLED,
                LifecycleStatus.EXPIRED_REGIME_SHIFT,
                LifecycleStatus.EXPIRED_SCORE_DECAY
            ]
            
            if is_terminal:
                signal.resolution_timestamp = now
                if new_status in [LifecycleStatus.EXPIRED, LifecycleStatus.EXPIRED_REGIME_SHIFT, LifecycleStatus.EXPIRED_SCORE_DECAY]:
                    signal.expiration_reason = reason
                
                # Record outcome metrics for terminal signals
                try:
                    await self._record_outcome_metrics(signal, db, provider)
                    # Trigger ML Forensic Analysis
                    await forensic_service.trigger_signal_analysis(str(signal.id))
                    # Periodically check for batch report
                    await forensic_service.check_and_trigger_batch_report(db)
                except Exception as e:
                    logger.error(f"[LifecycleService] Failed to record outcome metrics for {signal.id}: {e}")

            # Log Audit Event
            db.add(SignalAuditEvent(
                signal_id=signal.id,
                previous_state=old_status.value if hasattr(old_status, 'value') else str(old_status),
                new_state=new_status.value if hasattr(new_status, 'value') else str(new_status),
                reason=reason,
                triggered_by="LIFECYCLE_SERVICE"
            ))
            
            # Broadcast Update
            await ws_manager.broadcast("signals", {
                "eventType": "SIGNAL_UPDATE",
                "signalId": str(signal.id),
                "symbol": symbol,
                "status": new_status.value if hasattr(new_status, 'value') else str(new_status),
                "reason": reason,
                "timestamp": now.isoformat()
            })

    async def _record_outcome_metrics(self, signal: Signal, db: AsyncSession, provider: Any):
        """Calculates and stores MFE, MAE, Slippage and other forensic metrics."""
        start_time = signal.executed_at or signal.valid_from
        end_time = signal.resolution_timestamp or datetime.utcnow()
        
        if not start_time:
            return

        # 1. Fetch historical candles for the duration of the 'trade' or signal life
        # For simplicity, we fetch what we need to calculate MFE/MAE
        symbol = signal.asset.symbol
        # limit is a rough estimate, ideally we'd fetch by time range
        candles = await provider.fetch_ohlcv(symbol, "M1", 500) 
        
        relevant_candles = [
            c for c in candles 
            if start_time <= c["timestamp"] <= end_time
        ]
        
        if not relevant_candles:
            return

        prices = [c["high"] for c in relevant_candles] + [c["low"] for c in relevant_candles]
        if not prices:
            return

        entry = signal.execution_price or signal.entry_price
        is_buy = signal.direction.value == "BUY" if hasattr(signal.direction, 'value') else signal.direction == "BUY"
        
        if is_buy:
            signal.mfe = max([c["high"] for c in relevant_candles]) - entry
            signal.mae = entry - min([c["low"] for c in relevant_candles])
        else:
            signal.mfe = entry - min([c["low"] for c in relevant_candles])
            signal.mae = max([c["high"] for c in relevant_candles]) - entry

        # 2. Slippage calculation (if executed)
        if signal.executed_at and signal.execution_price:
            signal.slippage = abs(signal.execution_price - signal.entry_price)
            # Placeholder for latency
            signal.execution_latency_ms = 45 # Mock latency

        # 3. Regime shift check
        if signal.regime_at_expiration and signal.regime_at_expiration != signal.regime:
            signal.regime_shift_during_trade = True

        # 4. R-Multiple calculation
        # Normalized R = (Exit - Entry) / (Initial SL - Entry)
        # We need the exit price. For mock data, we use the last candle close.
        exit_price = relevant_candles[-1]["close"]
        risk = abs(signal.stop_loss - signal.entry_price)
        if risk > 0:
            pnl = (exit_price - entry) if is_buy else (entry - exit_price)
            signal.r_multiple_achieved = pnl / risk

    async def start_monitoring(self):
        """Infinite loop for the monitoring task."""
        from app.db.database import async_session
        while True:
            try:
                async with async_session() as db:
                    await self.run_cycle(db)
            except Exception as e:
                logger.error(f"[LifecycleService] Critical error in monitor loop: {e}")
            await asyncio.sleep(self.evaluation_interval)

# Singleton instance
lifecycle_service = SignalLifecycleService()
