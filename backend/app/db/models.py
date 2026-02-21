"""SQLAlchemy ORM models for VIL."""

import enum
from datetime import datetime
import uuid
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AccountType(str, enum.Enum):
    DEMO = "demo"
    LIVE = "live"


class BrokerEnvironment(str, enum.Enum):
    PRACTICE = "practice"
    LIVE = "live"


class AssetType(str, enum.Enum):
    FOREX = "forex"
    CRYPTO = "crypto"
    INDEX = "index"
    COMMODITY = "commodity"
    METAL = "metal"


class SignalDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class SignalClassification(str, enum.Enum):
    LOG_ONLY = "LOG_ONLY"
    REDUCED_SIZE = "REDUCED_SIZE"
    FULL_SIGNAL = "FULL_SIGNAL"


class LifecycleStatus(str, enum.Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    DROPPED = "DROPPED"
    SUPPRESSED = "SUPPRESSED"
    EXPIRED_REGIME_SHIFT = "EXPIRED_REGIME_SHIFT"
    EXPIRED_SCORE_DECAY = "EXPIRED_SCORE_DECAY"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class MarketRegime(str, enum.Enum):
    TRENDING_BULLISH = "TRENDING_BULLISH"
    TRENDING_BEARISH = "TRENDING_BEARISH"
    RANGING_WIDE = "RANGING_WIDE"
    RANGING_NARROW = "RANGING_NARROW"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    UNSTABLE = "UNSTABLE"
    EVENT_RISK = "EVENT_RISK"
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    LOW_ACTIVITY = "LOW_ACTIVITY"


class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED_OUT = "STOPPED_OUT"
    TP_HIT = "TP_HIT"


class Timeframe(str, enum.Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"


# ── Models ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    phone = Column(String(30), nullable=True)
    country = Column(String(100), nullable=True)
    account_type = Column(Enum(AccountType), default=AccountType.DEMO, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # Verification & Status
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)

    # Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # Legal
    terms_accepted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    trades = relationship("Trade", back_populates="user", lazy="selectin")
    broker_accounts = relationship("BrokerAccount", back_populates="user", lazy="selectin")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="selectin")


class BrokerAccount(Base):
    """Per-user encrypted OANDA broker credentials."""
    __tablename__ = "broker_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    broker_name = Column(String(50), default="oanda", nullable=False)
    account_id = Column(String(100), nullable=False)
    encrypted_api_key = Column(LargeBinary, nullable=False)
    encryption_iv = Column(LargeBinary, nullable=False)
    encryption_tag = Column(LargeBinary, nullable=False)
    environment = Column(Enum(BrokerEnvironment), default=BrokerEnvironment.PRACTICE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    account_currency = Column(String(10), default="USD", nullable=True)

    # Cached sync data
    last_synced_at = Column(DateTime, nullable=True)
    cached_balance = Column(Float, nullable=True)
    cached_equity = Column(Float, nullable=True)
    cached_margin_used = Column(Float, nullable=True)
    cached_open_trade_count = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="broker_accounts")


class RefreshToken(Base):
    """JWT refresh token storage for rotation & revocation."""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by = Column(String(255), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    """Immutable log of all security-sensitive actions."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    payload_hash = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="success")
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    base_currency = Column(String(10), nullable=False)
    quote_currency = Column(String(10), nullable=False)
    description = Column(String(200), nullable=True)

    signals = relationship("Signal", back_populates="asset", lazy="selectin")
    market_data = relationship("MarketData", back_populates="asset", lazy="selectin")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    direction = Column(Enum(SignalDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    score_delta = Column(Float, nullable=False, default=0.0)
    classification = Column(Enum(SignalClassification), default=SignalClassification.LOG_ONLY, nullable=False)
    regime = Column(Enum(MarketRegime), nullable=True)
    status = Column(Enum(LifecycleStatus), default=LifecycleStatus.PENDING, nullable=False, index=True)
    
    # Composition Scores
    regime_score = Column(Float, nullable=True)
    structure_score = Column(Float, nullable=True)
    volatility_score = Column(Float, nullable=True)
    liquidity_score = Column(Float, nullable=True)
    event_score = Column(Float, nullable=True)

    risk_reward = Column(Float, nullable=True)
    position_size = Column(Float, nullable=True)
    
    # Traceability & Execution
    broker_order_id = Column(String(50), nullable=True)
    execution_price = Column(Float, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_mode = Column(String(20), default="AUTO", nullable=False)
    execution_source = Column(String(50), default="OANDA_API", nullable=False)

    # ── Institutional Governance & ML Lineage ──
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True, index=True)
    entry_window_until = Column(DateTime, nullable=True)
    resolution_timestamp = Column(DateTime, nullable=True) # Closed/Dropped/Suppressed
    equity_at_entry = Column(Float, nullable=True)
    
    expiration_reason = Column(String(100), nullable=True)
    failure_category = Column(String(50), nullable=True)
    score_at_expiration = Column(Float, nullable=True)
    regime_at_expiration = Column(Enum(MarketRegime), nullable=True)
    signal_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    signal_version = Column(Integer, default=1)
    engine_version_hash = Column(String(64), nullable=True)
    decay_rate = Column(Float, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    
    # ── ML Inference Metadata ──
    ml_probability = Column(Float, nullable=True)
    ml_confidence = Column(Float, nullable=True)
    confidence_multiplier = Column(Float, default=1.0)
    risk_allocation = Column(Float, nullable=True) # Percentage or units
    model_version = Column(String(50), nullable=True)

    # ── Outcome Metrics (Forensics) ──
    r_multiple_achieved = Column(Float, nullable=True)
    mfe = Column(Float, nullable=True) # Max Favorable Excursion
    mae = Column(Float, nullable=True) # Max Adverse Excursion
    slippage = Column(Float, nullable=True)
    execution_latency_ms = Column(Integer, nullable=True)
    regime_shift_during_trade = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    asset = relationship("Asset", back_populates="signals", lazy="selectin")
    ai_reports = relationship("AIReport", back_populates="signal", lazy="selectin")
    trades = relationship("Trade", back_populates="signal", lazy="selectin")
    feature_snapshots = relationship("SignalFeatureSnapshot", back_populates="signal", lazy="selectin")
    audit_events = relationship("SignalAuditEvent", back_populates="signal", lazy="selectin")


class SignalFeatureSnapshot(Base):
    """Deep ML feature capture for forensic analysis."""
    __tablename__ = "signal_feature_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    
    regime_state = Column(String(50))
    volatility_percentile = Column(Float)
    atr = Column(Float)
    session = Column(String(20))
    liquidity_sweep_flag = Column(Integer)
    liquidity_zone_status = Column(String(50)) # e.g. "INSIDE_ZONE", "SWEEP", "CLEAN"
    spread_at_creation = Column(Float)
    event_proximity_score = Column(Float)
    structural_break_type = Column(String(50))
    correlation_snapshot = Column(Text)
    
    # Technical Indicators
    ema_fast = Column(Float, nullable=True)
    ema_slow = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    volume_spike_flag = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    signal = relationship("Signal", back_populates="feature_snapshots")


class SignalAuditEvent(Base):
    """Immutable log of state transitions."""
    __tablename__ = "signal_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    
    previous_state = Column(String(50))
    new_state = Column(String(50))
    reason = Column(String(255))
    triggered_by = Column(String(50))
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    signal = relationship("Signal", back_populates="audit_events")


class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    summary = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    risk_assessment = Column(Text, nullable=True)
    snapshot_url = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    signal = relationship("Signal", back_populates="ai_reports", lazy="selectin")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN, nullable=False)
    pnl = Column(Float, nullable=True)
    lots = Column(Float, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    signal = relationship("Signal", back_populates="trades", lazy="selectin")
    user = relationship("User", back_populates="trades", lazy="selectin")


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    timeframe = Column(Enum(Timeframe), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    asset = relationship("Asset", back_populates="market_data", lazy="selectin")


class ModelRegistry(Base):
    """Central repository for quant models."""
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    regime_type = Column(Enum(MarketRegime), nullable=True)
    features_hash = Column(String(64), nullable=True)
    roc_auc = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    is_active = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MLSignalDataset(Base):
    """The master training/validation set (Closed Loop)."""
    __tablename__ = "ml_signal_dataset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False, unique=True)
    
    features_json = Column(Text, nullable=False)
    
    target_reached = Column(Integer, nullable=True)
    target_reached = Column(Integer, nullable=True)
    stop_hit = Column(Integer, nullable=True)
    r_multiple = Column(Float, nullable=True)
    failure_classification = Column(String(50), nullable=True)
    
    is_training_sample = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SignalForensicAnalysis(Base):
    """Deep ML-driven analysis of a terminal signal."""
    __tablename__ = "signal_forensic_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False, unique=True)
    
    # Intelligence Scores (0-100)
    quality_score = Column(Float)
    execution_quality_score = Column(Float)
    structural_integrity_score = Column(Float)
    regime_compatibility_score = Column(Float)
    ml_confidence_deviation = Column(Float)

    # Textual Analysis
    causality_summary = Column(Text) # "Why did it win/lose?"
    engine_critique = Column(Text)   # "Was score inflated?"
    suggested_adjustments = Column(Text)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    engine_version_at_analysis = Column(String(64))

    signal = relationship("Signal")


class SignalIntelligenceReport(Base):
    """Batch report generated after every 50+ signals."""
    __tablename__ = "signal_intelligence_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    batch_start_date = Column(DateTime)
    batch_end_date = Column(DateTime)
    signal_count = Column(Integer)
    
    # High-level summary
    executive_summary = Column(Text)
    expectancy = Column(Float)
    
    # Statistical breakdown (JSON strings)
    setup_efficiency_json = Column(Text)
    regime_performance_json = Column(Text)
    volatility_sensitivity_json = Column(Text)
    
    # Actionable insights
    engine_critique_summary = Column(Text)
    strategic_recommendations = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
