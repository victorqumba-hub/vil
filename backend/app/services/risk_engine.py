"""Risk & Position Engine — Computes SL, TP, R:R, and position sizing.

Uses ATR-based stop-loss, structural levels, and account risk rules
to determine optimal position parameters.
"""

from dataclasses import dataclass


@dataclass
class PositionParams:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    position_size: float  # in lots
    risk_amount: float    # in account currency
    pip_value: float
    sl_pips: float
    tp_pips: float


# ── ATR Multipliers by Regime ─────────────────────────────────────────────────

ATR_SL_MULTIPLIER = {
    "TRENDING":          1.5,
    "RANGING":           1.0,
    "HIGH_VOLATILITY":   2.0,
    "LOW_ACTIVITY":      0.8,
}

ATR_TP_MULTIPLIER = {
    "TRENDING":          3.0,  # Let winners run
    "RANGING":           2.0,  # Tighter targets
    "HIGH_VOLATILITY":   2.5,  # Balance risk
    "LOW_ACTIVITY":      1.5,  # Small targets
}


def compute_pip_value(symbol: str, price: float) -> float:
    """Approximated pip value — for proper implementation, use broker API."""
    sym = symbol.upper()
    # JPY pairs: 1 pip = 0.01
    if "JPY" in sym and "JP225" not in sym:
        return 0.01
    # Metals
    if sym.startswith("XAU"):
        return 0.1    # Gold: 1 pip = $0.10
    if sym.startswith("XAG"):
        return 0.01   # Silver
    if sym.startswith("XPT") or sym.startswith("XPD"):
        return 0.1    # Platinum / Palladium
    # Crypto
    if any(c in sym for c in ["BTC", "ETH", "LTC", "BCH"]):
        return 1.0    # Crypto: 1 pip = $1
    # Indices
    if any(idx in sym for idx in ["SPX500", "NAS100", "US30", "DE30", "UK100", "JP225", "AU200", "HK33", "EU50"]):
        return 1.0    # Index: 1 point
    # Commodities — energy
    if any(c in sym for c in ["BCO", "WTICO"]):
        return 0.01   # Crude oil
    if "NATGAS" in sym:
        return 0.001  # Natural gas
    # Commodities — agricultural
    if any(c in sym for c in ["WHEAT", "CORN", "SUGAR", "SOYBN"]):
        return 0.01
    # Exotic forex with large prices (ZAR, TRY, MXN)
    if any(c in sym for c in ["ZAR", "TRY", "MXN", "HKD"]):
        return 0.0001
    return 0.0001      # Standard forex pairs


def calculate_position(
    direction: str,
    entry: float,
    atr: float,
    regime: str,
    symbol: str,
    account_balance: float = 10000.0,
    risk_pct: float = 1.0,  # Risk 1% of account
    swing_high: float | None = None,
    swing_low: float | None = None,
) -> PositionParams:
    """
    Calculate complete position parameters.

    Args:
        direction: "BUY" or "SELL"
        entry: Entry price
        atr: Current ATR
        regime: Market regime string
        symbol: Asset symbol
        account_balance: Account size
        risk_pct: Percentage of account to risk (default 1%)
        swing_high: Optional structural resistance
        swing_low: Optional structural support
    """
    pip = compute_pip_value(symbol, entry)
    sl_mult = ATR_SL_MULTIPLIER.get(regime, 1.5)
    tp_mult = ATR_TP_MULTIPLIER.get(regime, 2.5)

    sl_distance = atr * sl_mult
    tp_distance = atr * tp_mult

    if direction == "BUY":
        stop_loss = entry - sl_distance
        take_profit = entry + tp_distance

        # Tighten SL to swing low if available and closer
        if swing_low and swing_low < entry:
            structural_sl = swing_low - (atr * 0.2)  # Buffer below structure
            if structural_sl > stop_loss:  # Only if tighter
                stop_loss = structural_sl
                sl_distance = entry - stop_loss

        # Extend TP to swing high if close
        if swing_high and swing_high > entry:
            if abs(swing_high - take_profit) < atr:
                take_profit = swing_high  # Target structural resistance
                tp_distance = take_profit - entry

    else:  # SELL
        stop_loss = entry + sl_distance
        take_profit = entry - tp_distance

        if swing_high and swing_high > entry:
            structural_sl = swing_high + (atr * 0.2)
            if structural_sl < stop_loss:
                stop_loss = structural_sl
                sl_distance = stop_loss - entry

        if swing_low and swing_low < entry:
            if abs(swing_low - take_profit) < atr:
                take_profit = swing_low
                tp_distance = entry - take_profit

    # Ensure minimum R:R of 1.0
    if tp_distance > 0 and sl_distance > 0:
        rr = tp_distance / sl_distance
    else:
        rr = 0.0

    if rr < 1.0 and sl_distance > 0:
        # Extend TP to achieve at least 1.5 R:R
        tp_distance = sl_distance * 1.5
        if direction == "BUY":
            take_profit = entry + tp_distance
        else:
            take_profit = entry - tp_distance
        rr = 1.5

    # ── Position Sizing ──────────────────────────────────────────────────
    risk_amount = account_balance * (risk_pct / 100)
    sl_pips = sl_distance / pip if pip else 0
    tp_pips = tp_distance / pip if pip else 0

    # Standard lot = 100,000 units for forex
    # pip_value_per_lot ≈ $10 for standard pairs, varies for crosses
    pip_val_per_lot = 10.0  # Simplified
    sym = symbol.upper()
    if "JPY" in sym and "JP225" not in sym:
        pip_val_per_lot = 6.67  # Approximate
    elif sym.startswith("XAU"):
        pip_val_per_lot = 10.0  # Gold
    elif sym.startswith("XAG"):
        pip_val_per_lot = 50.0  # Silver (5000oz lot)
    elif sym.startswith("XPT") or sym.startswith("XPD"):
        pip_val_per_lot = 10.0  # Platinum / Palladium
    elif any(c in sym for c in ["BTC", "ETH", "LTC", "BCH"]):
        pip_val_per_lot = 1.0   # Crypto (1 unit)
    elif any(idx in sym for idx in ["SPX500", "NAS100", "US30", "DE30", "UK100", "JP225", "AU200", "HK33", "EU50"]):
        pip_val_per_lot = 1.0   # Index CFD (per point)
    elif any(c in sym for c in ["BCO", "WTICO"]):
        pip_val_per_lot = 10.0  # Crude oil
    elif "NATGAS" in sym:
        pip_val_per_lot = 10.0  # Natural gas
    elif any(c in sym for c in ["WHEAT", "CORN", "SUGAR", "SOYBN"]):
        pip_val_per_lot = 10.0  # Agricultural

    if sl_pips > 0 and pip_val_per_lot > 0:
        lots = risk_amount / (sl_pips * pip_val_per_lot)
        lots = round(min(lots, 10.0), 2)  # Cap at 10 lots
        lots = max(lots, 0.01)  # Minimum micro lot
    else:
        lots = 0.01

    return PositionParams(
        entry=round(entry, 5),
        stop_loss=round(stop_loss, 5),
        take_profit=round(take_profit, 5),
        risk_reward=round(rr, 2),
        position_size=lots,
        risk_amount=round(risk_amount, 2),
        pip_value=pip,
        sl_pips=round(sl_pips, 1),
        tp_pips=round(tp_pips, 1),
    )


def validate_position(params: PositionParams, min_rr: float = 1.0, max_risk_pct: float = 2.0, account_balance: float = 10000.0) -> dict:
    """
    Validate position parameters against risk rules.

    Returns: {"valid": bool, "warnings": list[str]}
    """
    warnings = []

    if params.risk_reward < min_rr:
        warnings.append(f"R:R {params.risk_reward} below minimum {min_rr}")

    actual_risk_pct = (params.risk_amount / account_balance) * 100
    if actual_risk_pct > max_risk_pct:
        warnings.append(f"Risk {actual_risk_pct:.1f}% exceeds maximum {max_risk_pct}%")

    if params.sl_pips < 5:
        warnings.append("Stop loss too tight — may get stopped out by noise")

    if params.position_size > 5.0:
        warnings.append(f"Position size {params.position_size} lots is large — verify account margin")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
    }
