"""Master Orchestrator — Coordinates the full signal generation pipeline.

Pipeline flow:
  1. Data Ingestion  → Fetch OHLCV candles
  2. Pre-Selection   → Rank pairs by opportunity
  3. Indicators      → Compute ATR, ADX, RSI
  4. Regime Gates    → Run 6-layer filter
  5. Regime Classify → Determine market condition
  6. Signal Scoring  → BaseScore → EventScore → AdjustedScore
  7. Risk Engine     → SL, TP, R:R, position sizing
  8. Output          → Structured signal ready for API/WS
"""

from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import select, desc, update
from uuid import uuid4
from app.config import settings
from app.services.data_ingestion import (
    get_data_provider, 
    compute_atr, 
    compute_adx, 
    compute_rsi,
    compute_volatility_percentile,
    compute_relative_volume,
    get_session_state,
    compute_ema,
    compute_vwap
)
from app.services.preselection import rank_pairs
from app.services.regime_gates import run_all_gates
from app.services.regime_classifier import classify_regime, Regime
from app.services.signal_scorer import score_signal
from app.services.risk_engine import calculate_position, validate_position
from app.services.structure_engine import StructureEngine, StructuralBias
from app.services.pipeline_monitor import monitor
from app.db.database import async_session
from app.db.models import (
    Signal, 
    Asset, 
    SignalDirection, 
    MarketRegime, 
    SignalClassification, 
    LifecycleStatus,
    SignalFeatureSnapshot,
    SignalAuditEvent,
    MLSignalDataset
)
from app.services.asset_manager import AssetManager, AssetClass
from app.ml.engine import model_manager
import json
import asyncio
from app.ws.websocket import manager as ws_manager
from app.services.broker_service import broker


async def run_pipeline(
    symbols: list[str] | None = None,
    timeframe: str = "H1",
    candle_limit: int = 200,
    top_n: int = 6,
    account_balance: float = 10000.0,
    risk_pct: float = 1.0,
    min_score: float = 40.0,
    upcoming_events: list[dict] | None = None,
    minutes_to_event: int | None = None,
    db: Any = None,
) -> list[dict]:
    """
    Run the full signal generation pipeline.

    Returns a list of structured signal dicts, sorted by final score.
    """
    target_symbols = symbols or AssetManager.get_all_symbols()
    
    # Import locally to avoid circular deps if any, though ws_manager should be fine
    from app.ws.websocket import manager as ws_manager

    async def broadcast_scan_event(symbol: str, status: str, detail: str = ""):
        print(f"[Orchestrator] BROADCAST: {symbol} | {status} | {detail}")
        try:
            await ws_manager.broadcast("signals", {
                "eventType": "SCAN_EVENT",
                "symbol": symbol,
                "status": status,
                "detail": detail,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"[Orchestrator] Broadcast failed for {symbol}: {e}")
            pass # Non-critical

    provider_name = "oanda"
    
    monitor.update_status(
        status="running",
        message=f"Starting scan for {len(target_symbols)} symbols...",
        last_run_time=datetime.utcnow().isoformat()
    )
    print(f"[Orchestrator] STARTED scan for {len(target_symbols)} symbols.")

    if not settings.OANDA_API_KEY:
        error_msg = "OANDA_API_KEY is missing. Pipeline cannot run."
        print(f"[Orchestrator] CRITICAL: {error_msg}")
        monitor.update_status(
            status="error", 
            last_error=error_msg, 
            message="OANDA API key missing",
            last_failure_time=datetime.utcnow().isoformat()
        )
        return []
        
    # ── Layer 2: Pre-Selection (Ranked by Opportunity) ───────────────────
    # We scan ALL symbols but pick top candidates for deep analysis
    # NEW: We pick top 3 from EACH asset class to ensure diversity
    print(f"[Orchestrator] Ranking {len(target_symbols)} candidates...")
    
    # Broadcast early to show UI activity
    await ws_manager.broadcast("signals", {
        "eventType": "SCAN_EVENT",
        "symbol": "SYSTEM",
        "status": "RANKING",
        "detail": f"Ranking {len(target_symbols)} assets...",
        "timestamp": datetime.utcnow().isoformat()
    })

    ranked_all = await rank_pairs(target_symbols, provider_name=provider_name)
    
    # Selection Strategy: Balance Asset Classes
    class_buckets = {}
    selected_candidates = []
    
    for item in ranked_all:
        sym = item["symbol"]
        ac = AssetManager.get_asset_class(sym)
        if ac not in class_buckets: class_buckets[ac] = 0
        
        # Take up to 2 per class unless we have room for more
        if class_buckets[ac] < 2 or len(selected_candidates) < top_n:
            selected_candidates.append(sym)
            class_buckets[ac] += 1
            
        if len(selected_candidates) >= top_n * 2: # Max pool size for deep scan
            break

    print(f"[Orchestrator] Selected {len(selected_candidates)} candidates for deep scan: {selected_candidates}")

    provider = get_data_provider(provider_name)
    generated_signals = []

    # Instantiate VIL 2.0 Engines
    struct_engine = StructureEngine()

    def _calculate_dynamic_ttl(regime: Regime) -> float:
        """Calculates signal validity duration based on regime stability."""
        ttl_map = {
            Regime.TRENDING_BULLISH: 4.0,
            Regime.TRENDING_BEARISH: 4.0,
            Regime.RANGING_WIDE: 3.0,
            Regime.RANGING_NARROW: 2.0,
            Regime.VOLATILITY_EXPANSION: 1.0,
            Regime.HIGH_VOLATILITY: 0.5,
            Regime.UNSTABLE: 0.25,
            Regime.EVENT_RISK: 0.0
        }
        return ttl_map.get(regime, 2.0)

    # ── Step 1-7: Process each candidate ─────────────────────────────────
    for symbol in selected_candidates:
        # Throttle to avoid OANDA rate limits (120 req/s)
        await asyncio.sleep(0.1) 
        try:
            # Heartbeat: Scanning Started
            await broadcast_scan_event(symbol, "SCANNING", "Fetching Data")

            profile = AssetManager.get_profile(symbol)
            
            # ── Layer 1: Market Data Engine Upgrade ──────────────────────────
            # Fetch primary timeframe (e.g. H1)
            candles = await provider.fetch_ohlcv(symbol, timeframe, candle_limit)
            if len(candles) < 100:
                await broadcast_scan_event(symbol, "SKIPPED", "Insufficient Data")
                continue

            # Fetch secondary timeframe (HTF) for Layer 5 Confluence
            htf_timeframe = "H4" if timeframe == "H1" else "D1"
            htf_candles = await provider.fetch_ohlcv(symbol, htf_timeframe, 50)
            
            tick = await provider.fetch_tick(symbol)
            current_spread = tick["ask"] - tick["bid"]

            # Compute Indicators
            atr_vals = compute_atr(candles, period=profile.atr_period)
            adx_vals = compute_adx(candles, period=profile.atr_period)
            rsi_vals = compute_rsi(candles, period=profile.atr_period)

            closes = [c["close"] for c in candles]
            highs = [c["high"] for c in candles]
            lows = [c["low"] for c in candles]
            price = closes[-1]
            atr = atr_vals[-1] * profile.volatility_multiplier
            adx = adx_vals[-1]
            
            # New Layer 1 Metrics
            vol_perc = compute_volatility_percentile(atr_vals)
            rel_vol = compute_relative_volume(candles)
            session_info = get_session_state(datetime.utcnow().hour)
            
            # Additional Indicators for Forensics
            ema_20 = compute_ema(candles, 20)
            ema_50 = compute_ema(candles, 50)
            vwap_vals = compute_vwap(candles)
            
            # Volume Spike Detection (> 3.0 relative volume)
            volume_spike = rel_vol > 3.0

            # ── Layer 2: Regime Intelligence (MAJOR UPGRADE) ────────────────
            regime_result = classify_regime(
                closes=closes,
                adx=adx,
                atr=atr,
                vol_percentile=vol_perc,
                rel_volume=rel_vol,
                minutes_to_event=minutes_to_event,
                sensitivity=profile.regime_sensitivity,
            )
            regime = regime_result["regime"]
            if regime == Regime.EVENT_RISK:
                await broadcast_scan_event(symbol, "REJECTED", "Event Risk")
                continue 

            # ── Layer 3: Structural Detection Engine ────────────────────────
            struct_result = struct_engine.detect_structure(candles)
            direction = "BUY" if struct_result.bias == StructuralBias.BULLISH else ("SELL" if struct_result.bias == StructuralBias.BEARISH else "NEUTRAL")

            # ── Layer 5: Multi-Timeframe Confluence Engine ──────────────────
            htf_struct = struct_engine.detect_structure(htf_candles)
            conf_score = 50.0
            if htf_struct.bias == struct_result.bias and struct_result.bias != StructuralBias.NEUTRAL:
                conf_score = 100.0  # Perfect alignment
            elif htf_struct.bias != struct_result.bias and htf_struct.bias != StructuralBias.NEUTRAL:
                conf_score = 20.0   # Misalignment penalty

            # ── Layer 6: Adaptive Scoring Engine ────────────────────────────
            # Calculate Event Risk Score
            ev_score = 100.0
            if minutes_to_event is not None:
                if minutes_to_event < 60: ev_score = 30.0
                elif minutes_to_event < 180: ev_score = 70.0

            scores = score_signal(
                regime_type=regime,
                regime_confidence=regime_result["confidence"],
                structure_score=struct_result.strength,
                confluence_score=conf_score,
                volatility_score=100.0 - vol_perc, # Low/Normal vol is better for setups
                liquidity_score=100.0 if struct_result.liquidity_sweep else 50.0,
                event_risk_score=ev_score,
                asset_profile_weights=profile.dict(),
            )
            
            final_score = scores["final_score"]
            if final_score < min_score:
                await broadcast_scan_event(symbol, "REJECTED", f"Score {final_score:.1f} < {min_score}")
                continue

            # ── Layer 7: Confidence & Risk Engine ───────────────────────────
            classification = SignalClassification.LOG_ONLY
            is_flagship = symbol in ["XAU_USD", "BTC_USD", "SPX500_USD", "NAS100_USD"]
            threshold = 75 if is_flagship else 80
            
            if final_score >= threshold:
                classification = SignalClassification.FULL_SIGNAL
            elif final_score >= 60:
                classification = SignalClassification.REDUCED_SIZE

            # Position sizing with Confidence Multiplier
            risk_mult = final_score / 100.0
            position = calculate_position(
                direction=direction,
                entry=price,
                atr=atr,
                regime=regime.value if hasattr(regime, 'value') else regime,
                symbol=symbol,
                account_balance=account_balance,
                risk_pct=risk_pct * profile.risk_reduction_coeff * risk_mult,
                swing_high=max(highs[-20:]) if len(highs) >= 20 else None,
                swing_low=min(lows[-20:]) if len(lows) >= 20 else None,
            )

            # ── Layer 8-9: Feature Snapshot & Signal Object ─────────────────
            feature_data = {
                "regime_state": str(regime),
                "regime_stability": regime_result.get("stability", 0),
                "volatility_percentile": vol_perc,
                "atr": round(atr, 5),
                "session": session_info["session"],
                "liquidity_sweep_flag": 1 if struct_result.liquidity_sweep else 0,
                "liquidity_zone_status": "SWEEP" if struct_result.liquidity_sweep else "CLEAN",
                "displacement_score": struct_result.displacement_score,
                "structural_bias": str(struct_result.bias),
                "mtf_alignment_score": conf_score,
                "spread_at_creation": current_spread,
                "event_proximity_score": ev_score,
                "structural_break_type": str(struct_result.bias),
                "correlation_snapshot": "{}",
                "ema_fast": ema_20[-1],
                "ema_slow": ema_50[-1],
                "rsi": rsi_vals[-1],
                "vwap": vwap_vals[-1],
                "volume_spike_flag": volume_spike
            }

            # ── Score Delta Calculation ───────────────────────────────
            score_delta = 0.0
            if db:
                # Find the latest signal for this symbol
                last_sig_query = (
                    select(Signal)
                    .join(Asset)
                    .where(Asset.symbol == symbol)
                    .order_by(desc(Signal.timestamp))
                    .limit(1)
                )
                last_sig_res = await db.execute(last_sig_query)
                last_member = last_sig_res.scalar_one_or_none()
                if last_member:
                    score_delta = final_score - last_member.score

            signal = {
                "symbol": symbol,
                "asset_class": profile.asset_class.value,
                "tier": profile.tier,
                "direction": direction,
                "entry_price": position.entry,
                "stop_loss": position.stop_loss,
                "take_profit": position.take_profit,
                "risk_reward": position.risk_reward,
                "position_size": position.position_size,
                "score": final_score,
                "score_delta": score_delta,
                "classification": classification.value,
                "regime": regime.value if hasattr(regime, 'value') else str(regime),
                "ttl_hours": _calculate_dynamic_ttl(regime),
                "status": LifecycleStatus.CREATED.value,
                "timestamp": datetime.utcnow().isoformat(),
                "scoring": scores,
                "regime_detail": regime_result,
                "structure_detail": {
                    "bias": str(struct_result.bias),
                    "strength": struct_result.strength,
                    "last_bos": struct_result.last_bos,
                    "last_choch": struct_result.last_choch
                },
                "features": feature_data
            }

            await broadcast_scan_event(symbol, "GENERATED", f"VIL 2.0 Signal ({final_score:.1f})")
            generated_signals.append(signal)

        except Exception as e:
            print(f"[Orchestrator] VIL 2.0 Error for {symbol}: {e}")
            continue

    # Sort by score descending
    generated_signals.sort(key=lambda s: s["score"], reverse=True)

    # ── Layer 10 & 11: Persistence & Execution ────────────────────────────────
    if target_symbols:
        # Use provided DB session OR create a local one for this unit of work
        db_context = None
        if db is None:
            db_context = async_session()
        
        session = db or db_context
        
        try:
            # ── Layer 10: Persistence & Superseding ──
            # 1. Supersede old PENDING signals for scanned symbols
            print(f"[Orchestrator] Superseding old PENDING signals for {len(target_symbols)} symbols...")
            subq = (
                select(Signal.id)
                .join(Asset)
                .where(Asset.symbol.in_(target_symbols))
                .where(Signal.status == LifecycleStatus.PENDING)
            )
            res = await session.execute(subq)
            ids_to_drop = [r[0] for r in res.all()]
            
            if ids_to_drop:
                print(f"[Orchestrator] Dropping {len(ids_to_drop)} superseded signals...")
                stmt = (
                    update(Signal)
                    .where(Signal.id.in_(ids_to_drop))
                    .values(
                        status=LifecycleStatus.DROPPED,
                        notes="Superseded by fresh scan"
                    )
                )
                await session.execute(stmt)
            
            if generated_signals:
                print(f"[Orchestrator] Persisting {len(generated_signals)} signals to DB...")
                for s_data in generated_signals:
                    # 10.1: Intake Governance (Versioning & Suppression)
                    asset_result = await session.execute(select(Asset).where(Asset.symbol == s_data["symbol"]))
                    asset = asset_result.scalar_one_or_none()
                    if not asset: continue

                    # Check for active trade
                    positions = await broker.get_positions()
                    has_active = any(p.get("instrument") == s_data["symbol"].replace("/", "_") for p in positions)
                    
                    final_status = LifecycleStatus.PENDING
                    suppression_note = None
                    if has_active:
                        final_status = LifecycleStatus.SUPPRESSED
                        suppression_note = "Active trade exists for this instrument"

                    # Find existing group or start new
                    find_group_query = (
                        select(Signal)
                        .where(Signal.asset_id == asset.id)
                        .where(Signal.status == LifecycleStatus.DROPPED)
                        .where(Signal.notes == "Superseded by fresh scan")
                        .order_by(desc(Signal.timestamp))
                        .limit(1)
                    )
                    group_res = await session.execute(find_group_query)
                    last_member = group_res.scalar_one_or_none()
                    
                    group_id = last_member.signal_group_id if last_member else uuid4()
                    version = (last_member.signal_version + 1) if last_member else 1

                    # 10.2: Object Creation & Audit
                    new_signal = Signal(
                        asset_id=asset.id,
                        direction=SignalDirection.BUY if s_data["direction"] == "BUY" else SignalDirection.SELL,
                        entry_price=s_data["entry_price"],
                        stop_loss=s_data["stop_loss"],
                        take_profit=s_data["take_profit"],
                        score=s_data["score"],
                        score_delta=s_data["score_delta"],
                        classification=SignalClassification(s_data["classification"]),
                        regime=MarketRegime(s_data["regime"]) if s_data["regime"] else None,
                        status=final_status,
                        regime_score=s_data["scoring"]["components"]["regime"],
                        structure_score=s_data["scoring"]["components"]["structure"],
                        volatility_score=s_data["scoring"]["components"]["volatility"],
                        liquidity_score=s_data["scoring"]["components"]["liquidity"],
                        event_score=s_data["scoring"]["components"]["event"],
                        risk_reward=s_data["risk_reward"],
                        position_size=s_data["position_size"],
                        equity_at_entry=account_balance, # From pipeline arg
                        confidence_multiplier=risk_mult,
                        risk_allocation=risk_pct * profile.risk_reduction_coeff * risk_mult,
                        engine_version_hash="v3.0-forensic-alpha",
                        valid_from=datetime.utcnow(),
                        valid_until=datetime.utcnow() + timedelta(hours=s_data["ttl_hours"]),
                        signal_group_id=group_id,
                        signal_version=version,
                        notes=suppression_note or s_data.get("notes"),
                        timestamp=datetime.fromisoformat(s_data["timestamp"])
                    )

                    # ── Layer 10.3: ML Augmentation & Feature Store ──
                    # 1. Build Feature Vector v1.0
                    ml_features = {
                        "symbol": s_data["symbol"],
                        "regime": s_data["regime"] or "UNKNOWN",
                        "direction": s_data["direction"],
                        "score": s_data["score"],
                        "structure_score": s_data["scoring"]["components"]["structure"],
                        "volatility_score": s_data["scoring"]["components"]["volatility"],
                        "liquidity_score": s_data["scoring"]["components"]["liquidity"],
                        "event_score": s_data["scoring"]["components"]["event"],
                        "adx": s_data.get("features", {}).get("adx", 25.0), # Placeholders if missing
                        "rsi": s_data.get("features", {}).get("rsi", 50.0),
                        "atr_percentile": s_data.get("features", {}).get("atr_percentile", 0.5),
                        "relative_volume": s_data.get("features", {}).get("relative_volume", 1.0),
                        "session_rank": 1,
                        "hour_of_day": datetime.utcnow().hour,
                        "day_of_week": datetime.utcnow().weekday()
                    }

                    # 2. Call ML Inference Service (Predict Success)
                    ml_result = model_manager.predict(ml_features)
                    if ml_result:
                        new_signal.ml_probability = ml_result["prob"]
                        new_signal.ml_confidence = ml_result["confidence"]
                        new_signal.model_version = ml_result["version"]
                        print(f"[Orchestrator] ML AUGMENT: {s_data['symbol']} -> Prob: {new_signal.ml_probability}")
                    else:
                        print(f"[Orchestrator] ML FALLBACK: ML Engine error for {s_data['symbol']}. Using base scores.")

                    # 3. Store in Feature Store (MLSignalDataset)
                    session.add(new_signal)
                    await session.flush() # Get ID
                    
                    s_data["id"] = new_signal.id

                    session.add(MLSignalDataset(
                        signal_id=new_signal.id,
                        features_json=json.dumps(ml_features),
                        is_training_sample=0 # Fresh signals are for inference/val
                    ))

                    # Audit
                    session.add(SignalAuditEvent(signal_id=new_signal.id, previous_state=None, new_state="CREATED", reason="Intake", triggered_by="ORCHESTRATOR"))
                    session.add(SignalAuditEvent(signal_id=new_signal.id, previous_state="CREATED", new_state="VALIDATED", reason="Governance Check Passed", triggered_by="ORCHESTRATOR"))
                    
                    # Features
                    feat = s_data["features"]
                    session.add(SignalFeatureSnapshot(
                        signal_id=new_signal.id,
                        regime_state=feat["regime_state"],
                        volatility_percentile=feat["volatility_percentile"],
                        atr=feat["atr"],
                        session=feat["session"],
                        liquidity_sweep_flag=feat["liquidity_sweep_flag"],
                        spread_at_creation=feat["spread_at_creation"],
                        event_proximity_score=feat["event_proximity_score"],
                        structural_break_type=feat["structural_break_type"],
                        correlation_snapshot=feat["correlation_snapshot"],
                        liquidity_zone_status=feat["liquidity_zone_status"],
                        ema_fast=feat["ema_fast"],
                        ema_slow=feat["ema_slow"],
                        rsi=feat["rsi"],
                        vwap=feat["vwap"],
                        volume_spike_flag=feat["volume_spike_flag"]
                    ))

                    # Broadcast
                    await ws_manager.broadcast("signals", {
                        "eventType": "SIGNAL_CREATED",
                        "signalId": str(new_signal.id),
                        "symbol": s_data["symbol"],
                        "direction": s_data["direction"],
                        "score": s_data["score"],
                        "regime": s_data["regime"],
                        "classification": s_data["classification"],
                        "assetClass": s_data.get("asset_class"),
                        "status": final_status.value,
                        "ml_probability": new_signal.ml_probability,
                        "ml_confidence": new_signal.ml_confidence,
                        "model_version": new_signal.model_version,
                        "timestamp": s_data["timestamp"],
                        "version": version
                    })

            # ── Layer 11: Automated Execution ──
            for s_data in generated_signals:
                if s_data["classification"] in [SignalClassification.FULL_SIGNAL.value, SignalClassification.REDUCED_SIZE.value]:
                    print(f"[Orchestrator] AUTOMATION: Guardrail Verification for {s_data['symbol']}...")
                    
                    # 1. Re-validate Signal in DB
                    sig_verify_query = (
                        select(Signal)
                        .join(Asset)
                        .where(Asset.symbol == s_data["symbol"])
                        .order_by(desc(Signal.timestamp))
                        .limit(1)
                    )
                    verify_res = await session.execute(sig_verify_query)
                    sig_to_trade = verify_res.scalar_one_or_none()
                    
                    if not sig_to_trade or sig_to_trade.status != LifecycleStatus.PENDING:
                        print(f"[Orchestrator] GAURDRAIL: Aborting. Status is {sig_to_trade.status if sig_to_trade else 'REMOVED'}")
                        continue

                    if sig_to_trade.valid_until and datetime.utcnow() > sig_to_trade.valid_until:
                        print(f"[Orchestrator] GAURDRAIL: Aborting. TTL Expired.")
                        session.add(SignalAuditEvent(signal_id=sig_to_trade.id, previous_state="PENDING", new_state="EXPIRED", reason="Execution Guardrail: TTL Expired", triggered_by="EXECUTION_GUARDRAIL"))
                        sig_to_trade.status = LifecycleStatus.EXPIRED
                        continue

                    if sig_to_trade.score < min_score:
                        print(f"[Orchestrator] GAURDRAIL: Aborting. Score {sig_to_trade.score} < {min_score}")
                        session.add(SignalAuditEvent(signal_id=sig_to_trade.id, previous_state="PENDING", new_state="DROPPED", reason="Execution Guardrail: Score decayed below threshold", triggered_by="EXECUTION_GUARDRAIL"))
                        sig_to_trade.status = LifecycleStatus.DROPPED
                        continue

                    # 2. Check for existing positions
                    positions = await broker.get_positions()
                    existing = [p for p in positions if p.get("instrument") == s_data["symbol"].replace("/", "_")]
                    if existing:
                        print(f"[Orchestrator] SKIP: Position already exists for {s_data['symbol']}.")
                        continue

                    # 3. Place Order
                    asset_class = s_data.get("asset_class", "forex")
                    lots = s_data["position_size"]
                    
                    if asset_class == "forex":
                        units = int(lots * 100_000)
                    elif asset_class == "metal":
                        units = int(lots * 100)
                    else:
                        units = int(lots)
                    
                    if units == 0: units = 1
                    
                    print(f"[Orchestrator] Sending Order: {s_data['symbol']} {s_data['direction']} {units} units")
                    order_res = await broker.place_order(
                        symbol=s_data["symbol"],
                        direction=s_data["direction"],
                        entry=s_data["entry_price"],
                        stop_loss=s_data["stop_loss"],
                        take_profit=s_data["take_profit"],
                        units=units
                    )

                    # 4. Update DB Status
                    if order_res.status == "EXECUTED":
                        sig_to_trade.status = LifecycleStatus.ACTIVE
                        sig_to_trade.execution_price = order_res.entry
                        sig_to_trade.broker_order_id = order_res.order_id
                        sig_to_trade.executed_at = datetime.utcnow()
                        sig_to_trade.execution_mode = "AUTO"
                        sig_to_trade.execution_source = "OANDA_API"
                        
                        session.add(SignalAuditEvent(signal_id=sig_to_trade.id, previous_state="PENDING", new_state="ACTIVE", reason="Order Executed", triggered_by="BROKER_SERVICE"))
                    
                    await broadcast_scan_event(s_data["symbol"], "EXECUTED" if order_res.status == "EXECUTED" else "EXEC_FAILED", order_res.message)

            if db_context:
                await session.commit()
                print(f"[Orchestrator] Local session committed.")
            else:
                await session.flush()
                print(f"[Orchestrator] External session flushed.")

        except Exception as e:
            print(f"[Orchestrator] Critical Execution Error: {e}")
            import traceback
            traceback.print_exc()
            if db_context: await session.rollback()
            monitor.update_status(status="error", last_error=str(e))
        finally:
            if db_context: await session.close()

    monitor.update_status(
        status="success",
        last_success_time=datetime.utcnow().isoformat(),
        processed_symbols=[s["symbol"] for s in generated_signals[:top_n]],
        message=f"Last scan completed successfully at {datetime.utcnow().strftime('%H:%M:%S')}"
    )

    return generated_signals
