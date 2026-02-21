"""Signal Lifecycle Manager — Monitors and updates signal states."""

from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Signal, Asset, LifecycleStatus, SignalClassification, MarketRegime
from app.services.data_ingestion import get_data_provider, compute_atr, compute_volatility_percentile
from app.services.regime_classifier import classify_regime
from app.services.ml_client import ml_client

class LifecycleManager:
    """Manages the lifecycle of generated signals."""

    def __init__(self):
        self.min_activation_score = 40.0
        self.expiration_hours = 4  # Reduced from 24 to 4 hours (Institutional standard for H1)

    async def update_lifecycles(self, db: AsyncSession):
        """
        Scan all non-terminal signals and update their status.
        PENDING -> ACTIVE (if entry hit)
        PENDING -> DROPPED (if score < threshold)
        PENDING -> EXPIRED (if timeout)
        ACTIVE -> SUCCEEDED (if TP hit)
        ACTIVE -> FAILED (if SL hit)
        """
        # Fetch non-terminal signals (PENDING or ACTIVE)
        query = select(Signal).where(
            Signal.status.in_([LifecycleStatus.PENDING, LifecycleStatus.ACTIVE])
        )
        result = await db.execute(query)
        signals = result.scalars().all()

        updates = []
        for signal in signals:
            try:
                # 1. Fetch current price
                if not hasattr(self, 'provider'):
                    self.provider = get_data_provider("oanda")
                
                symbol = signal.asset.symbol
                tick = await self.provider.fetch_tick(symbol)
                price = (tick["bid"] + tick["ask"]) / 2  # Mid-price

                new_status = signal.status

                # 2. Check Expiration
                if signal.status == LifecycleStatus.PENDING:
                    if datetime.utcnow() - signal.timestamp > timedelta(hours=self.expiration_hours):
                        new_status = LifecycleStatus.EXPIRED
                    
                    # 3. Check Scoring Deterioration
                    elif signal.score < self.min_activation_score:
                        new_status = LifecycleStatus.DROPPED
                    
                    # 4. Check Activation (Hit Entry)
                    else:
                        is_buy = signal.direction.value == "BUY"
                        if is_buy:
                            if price >= signal.entry_price:
                                new_status = LifecycleStatus.ACTIVE
                        else: # SELL
                            if price <= signal.entry_price:
                                new_status = LifecycleStatus.ACTIVE

                # 5. Check Outcome (If ACTIVE)
                if signal.status == LifecycleStatus.ACTIVE or new_status == LifecycleStatus.ACTIVE:
                    is_buy = signal.direction.value == "BUY"
                    hit_tp = (is_buy and price >= signal.take_profit) or (not is_buy and price <= signal.take_profit)
                    hit_sl = (is_buy and price <= signal.stop_loss) or (not is_buy and price >= signal.stop_loss)

                    if hit_tp:
                        new_status = LifecycleStatus.SUCCESS
                        # Log success outcome to ML service
                        await ml_client.log_outcome(signal.id, "SUCCESS", r_multiple=signal.risk_reward or 1.0)
                    elif hit_sl:
                        new_status = LifecycleStatus.FAILED
                        # ── Layer 11: Failure Classification ──
                        signal.failure_category = await self._classify_failure(signal, price)
                        # Log failure outcome to ML service
                        await ml_client.log_outcome(signal.id, "FAILED", r_multiple=-1.0)

                if new_status != signal.status:
                    signal.status = new_status
                    updates.append({
                        "id": signal.id,
                        "symbol": symbol,
                        "old_status": signal.status,
                        "new_status": new_status,
                        "price": price,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except Exception as e:
                print(f"[Lifecycle] Error updating {signal.asset.symbol}: {e}")

        if updates:
            await db.commit()
            print(f"[Lifecycle] Updated {len(updates)} signals.")
        
        return updates

    async def _classify_failure(self, signal: Signal, price: float) -> str:
        """Determines the root cause of a signal failure."""
        try:
            # Fetch recent context
            symbol = signal.asset.symbol
            candles = await self.provider.fetch_ohlcv(symbol, "H1", 24)
            closes = [c["close"] for c in candles]
            atr_vals = compute_atr(candles)
            vol_perc = compute_volatility_percentile(atr_vals)
            
            # Simple logic for now
            if str(signal.regime) == "TRENDING" and vol_perc > 80:
                return "VOLATILITY_SPIKE"
            
            # Check for regime shift using recent data
            # (In a real system we'd call classify_regime here)
            return "STANDARD_STOP_OUT"
        except:
            return "UNKNOWN"

lifecycle_manager = LifecycleManager()
