import { useMemo } from 'react'
import './SignalCard.css'

export default function SignalCard({ signal, mode, onViewMore, onDownload }) {
    const isBuy = signal.direction === 'BUY'

    // Format timer (mock logic or relative time)
    const timeElapsed = useMemo(() => {
        if (!signal.timestamp) return "00:00"
        try {
            const diff = Math.floor((new Date() - new Date(signal.timestamp)) / 1000)
            const mm = Math.floor(diff / 60).toString().padStart(2, '0')
            const ss = (diff % 60).toString().padStart(2, '0')
            return `${mm}:${ss}`
        } catch { return "00:00" }
    }, [signal.timestamp])

    const currencyIcon = signal.symbol ? signal.symbol.charAt(0) : '?'

    return (
        <div className="signal-card-new">
            {/* ── Header ────────────────────────────────────────────── */}
            <div className="sc-n-header">
                <div className="sc-n-icon-wrapper">
                    <div className={`sc-n-icon-circle ${isBuy ? 'buy-theme' : 'sell-theme'}`}>
                        {currencyIcon}
                    </div>
                </div>
                <div className="sc-n-info">
                    <h3>
                        {signal.symbol}
                        {signal.version > 1 && <span className="version-tag">v{signal.version}</span>}
                    </h3>
                    <span className="sc-n-meta">
                        <span className={`sc-n-class-tag ${signal.asset_class || 'forex'}`}>{(signal.asset_class || 'forex').toUpperCase()}</span>
                        • {(signal.status || 'PENDING').replace(/_/g, ' ')}
                    </span>
                </div>
                <div className={`sc-n-badge ${isBuy ? 'buy' : 'sell'}`}>
                    {signal.direction}
                </div>
            </div>

            {/* ── Price Grid ────────────────────────────────────────── */}
            <div className="sc-n-grid">
                <div className="sc-n-box entry">
                    <span className="sc-n-label">ENTRY</span>
                    <span className="sc-n-value">{signal.entry_price?.toFixed(4)}</span>
                </div>
                <div className="sc-n-box stop">
                    <span className="sc-n-label">STOP</span>
                    <span className="sc-n-value">{signal.stop_loss?.toFixed(4)}</span>
                </div>
                <div className="sc-n-box target">
                    <span className="sc-n-label">TARGET</span>
                    <span className="sc-n-value">{signal.take_profit?.toFixed(4)}</span>
                </div>
            </div>

            {/* ── Stats ─────────────────────────────────────────────── */}
            <div className="sc-n-stats">
                <div className="sc-n-stat-group">
                    <span className="stat-label">Score</span>
                    <span className={`stat-value ${signal.score >= 70 ? 'high' : 'med'}`}>{Math.round(signal.score)}</span>
                </div>
                <div className="sc-n-stat-group">
                    <span className="stat-label">R:R</span>
                    <span className="stat-value white">{signal.risk_reward || '1.5'}</span>
                </div>
                <div className="sc-n-progress-container">
                    <div className="sc-n-progress-bar" style={{ width: `${Math.min(signal.score, 100)}%` }} />
                </div>
            </div>

            {/* ── Regime / Status / Timer ────────────────────────────────────── */}
            <div className="sc-n-row-info">
                <div className="sc-n-regime" title="Signal State Name">
                    <span className="regime-label">Status:</span>
                    <span className={`regime-badge status-${(signal.status || 'pending').toLowerCase()}`}>
                        {(signal.status || 'PENDING').replace(/_/g, ' ')}
                    </span>
                </div>

                {signal.valid_until && (
                    <div className="sc-n-regime" title="Expiration Window">
                        <span className="regime-label">TTL:</span>
                        <span className="regime-badge ttl">
                            {new Date(signal.valid_until) > new Date() ? 'ACTIVE' : 'EXPIRED'}
                        </span>
                    </div>
                )}
            </div>

            <div className="sc-n-row-info">
                <div className="sc-n-regime">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-pulse">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                    <span className="regime-label">Regime:</span>
                    <span className={`regime-badge ${signal.regime === 'TRENDING' ? 'trending' : ''}`}>
                        {signal.regime || 'RANGE BOUND'}
                    </span>
                </div>
            </div>

            {/* ── Liquidity / Volatility ────────────────────────────── */}
            <div className="sc-n-row-info secondary">
                {signal.liquidity_detail && (
                    <>
                        <div className="sc-n-regime">
                            <span className="regime-label">Vol:</span>
                            <span className="regime-value">{signal.liquidity_detail.vol_state}</span>
                        </div>
                        {signal.liquidity_detail.sweep && (
                            <div className="sc-n-tag sweep-tag">
                                🧹 SWEEP
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* ── Actions ───────────────────────────────────────────── */}
            <div className="sc-n-actions">
                {mode === 'intelligence' ? (
                    <>
                        <button className="btn-approve" onClick={onViewMore}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
                            </svg>
                            View More
                        </button>
                        <button className="btn-reject" onClick={onDownload}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                            </svg>
                            Report
                        </button>
                    </>
                ) : (
                    <>
                        <button className="btn-approve">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Approve
                        </button>
                        <button className="btn-reject">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                            Reject
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}
