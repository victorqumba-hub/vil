import React from 'react';

export default function SignalIntelligenceItem({ signal, isSelected, onClick }) {
    const {
        symbol,
        score,
        scoreDelta,
        status,
        classification,
        regime,
        structuralConfidence,
        volatilityScore,
        liquidityScore,
        timestamp,
        direction,
        id
    } = signal;

    const timeStr = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Status CSS mapping
    const statusClass = `status-${(status || 'PENDING').toLowerCase()}`;
    const classificationClass = `classification-${(classification || 'LOG_ONLY').toLowerCase().replace('_', '-')}`;

    return (
        <div
            className={`signal-item animate-signal ${isSelected ? 'selected' : ''}`}
            onClick={() => onClick(signal)}
        >
            <div className="signal-item-header">
                <div>
                    <div className="signal-symbol">{symbol}</div>
                    <div className="signal-id">ID: {(id || '0x...').substring(0, 8)}</div>
                </div>
                <div className={`status-badge ${statusClass}`}>
                    {status}
                </div>
            </div>

            <div className="signal-metrics">
                <div className="metric">
                    <div className="metric-sub-label">Dir</div>
                    <div className={`metric-sub-value ${direction === 'BUY' ? 'delta-up' : 'delta-down'}`}>
                        {direction}
                    </div>
                </div>
                <div className="metric">
                    <div className="metric-sub-label">Regime</div>
                    <div className="metric-sub-value" style={{ fontSize: '0.7rem' }}>{regime}</div>
                </div>
                <div className="metric">
                    <div className="metric-sub-label">Time</div>
                    <div className="metric-sub-value" style={{ fontSize: '0.7rem', color: '#666' }}>{timeStr}</div>
                </div>
            </div>

            <div className="signal-score-row">
                <div className="score-main">{score}</div>
                {scoreDelta !== 0 && (
                    <div className={`score-delta ${scoreDelta > 0 ? 'delta-up' : 'delta-down'}`}>
                        {scoreDelta > 0 ? '↑' : '↓'} {Math.abs(scoreDelta)}
                    </div>
                )}
                <div className={`classification-tag ${classificationClass}`}>
                    {classification}
                </div>
            </div>

            {/* Heat Indicator Bar */}
            <div className="heat-indicator">
                <div className="heat-segment heat-regime" style={{ width: `${(signal.regime_score || 25)}%` }} title="Regime Alignment" />
                <div className="heat-segment heat-structure" style={{ width: `${(structuralConfidence || 25)}%` }} title="Structural Confirmation" />
                <div className="heat-segment heat-volatility" style={{ width: `${(volatilityScore || 25)}%` }} title="Volatility Alignment" />
                <div className="heat-segment heat-liquidity" style={{ width: `${(liquidityScore || 25)}%` }} title="Liquidity Confirmation" />
            </div>

            <div style={{ fontSize: '0.6rem', color: '#555', marginTop: '4px', display: 'flex', justifyContent: 'space-between' }}>
                <span>STRUCT: {structuralConfidence}%</span>
                <span>VOL: {volatilityScore}%</span>
            </div>
        </div>
    );
}
