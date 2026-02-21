import React, { useState, useEffect, useRef } from 'react';
import './LiveSignalStream.css';

/**
 * LiveSignalStream - Institutional Grade Signal Feed
 * 
 * Visualizes the OANDA pipeline as a living, breathing data stream.
 * Splits view into:
 * 1. Active Board: Current state of all active/pending signals (The "Monitor")
 * 2. Event Tape: Chronological log of changes (The "Flow")
 */
export default function LiveSignalStream({ signals = [], scanEvent, onSignalSelect, variant = 'desktop' }) {
    const [tapeEvents, setTapeEvents] = useState([]);
    const [scanTicker, setScanTicker] = useState(null);
    const prevSignalsRef = useRef(new Map());
    const isFirstRun = useRef(true);

    // ── Handle Scan Ticker ─────────────────────────────────────────────
    useEffect(() => {
        if (scanEvent) {
            setScanTicker(scanEvent);
            // Auto-clear after 2 seconds if no new event comes
            const timer = setTimeout(() => setScanTicker(null), 2000);
            return () => clearTimeout(timer);
        }
    }, [scanEvent]);

    // ── Diff Engine: Generate Events from Signal Updates ────────────────
    useEffect(() => {
        if (!Array.isArray(signals)) return;

        const validSignals = signals.filter(s => s && (s.signalId || s.id));
        const newSignalMap = new Map(validSignals.map(s => [s.signalId || s.id, s]));
        const events = [];
        const timestamp = new Date();

        // 1. Check for NEW signals and ALREADY EXISTING modifications
        validSignals.forEach(sig => {
            const id = sig.signalId || sig.id;
            const prev = prevSignalsRef.current.get(id);

            if (!prev) {
                // New Entry
                if (!isFirstRun.current) {
                    events.push({
                        id: `evt-${id}-new-${timestamp.getTime()}`,
                        type: 'ENTRY',
                        symbol: sig.symbol,
                        message: 'Entered Pipeline',
                        detail: `Score: ${sig.score?.toFixed(1) || '0.0'} | ${sig.direction || 'N/A'}`,
                        time: timestamp,
                        sentiment: 'neutral'
                    });
                }
            } else {
                // Modified?
                // Score Change
                if (sig.score !== undefined && prev.score !== undefined && Math.abs(sig.score - prev.score) > 0.1) {
                    const diff = sig.score - prev.score;
                    events.push({
                        id: `evt-${id}-score-${timestamp.getTime()}`,
                        type: 'SCORING',
                        symbol: sig.symbol,
                        message: 'Score Update',
                        detail: `${(prev.score || 0).toFixed(1)} → ${(sig.score || 0).toFixed(1)} (${diff > 0 ? '+' : ''}${diff.toFixed(1)})`,
                        time: timestamp,
                        sentiment: diff > 0 ? 'bullish' : 'bearish'
                    });
                }

                // Status Change
                if (sig.status !== prev.status) {
                    events.push({
                        id: `evt-${id}-status-${timestamp.getTime()}`,
                        type: 'LIFECYCLE',
                        symbol: sig.symbol,
                        message: 'Status Change',
                        detail: `${prev.status || 'PENDING'} → ${sig.status}`,
                        time: timestamp,
                        sentiment: sig.status === 'ACTIVE' ? 'bullish' : (sig.status === 'FAILED' ? 'bearish' : 'neutral')
                    });
                }
            }
        });

        // Update Ref
        prevSignalsRef.current = newSignalMap;
        isFirstRun.current = false;

        // Add events to tape (keep last 50)
        if (events.length > 0) {
            setTapeEvents(prev => [...events, ...prev].slice(0, 50));
        }

    }, [signals]);


    // ── Render Helpers ──────────────────────────────────────────────────

    const formatTime = (date) => {
        if (!(date instanceof Date)) return '--:--:--';
        return date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    const getScoreColor = (score) => {
        if (score >= 80) return '#00ff88'; // Strong
        if (score >= 50) return '#00e5ff'; // Moderate
        return '#6c757d'; // Weak
    };

    if (variant === 'mobile-condensed') {
        return (
            <div className="mobile-signal-list">
                {signals.filter(s => s && (s.signalId || s.id)).map((sig) => {
                    const id = sig.signalId || sig.id;
                    const isBuy = sig.direction === 'BUY';
                    return (
                        <div key={id} className="mobile-signal-card glass-card" onClick={() => onSignalSelect && onSignalSelect(sig)}>
                            <div className="sig-main">
                                <span className="sig-symbol">{sig.symbol}</span>
                                <span className={`sig-direction ${isBuy ? 'buy' : 'sell'}`}>{sig.direction}</span>
                            </div>
                            <div className="sig-stats">
                                <div className="sig-stat">
                                    <span className="l">Regime</span>
                                    <span className="v">{sig.regime || 'WAIT'}</span>
                                </div>
                                <div className="sig-stat">
                                    <span className="l">Score</span>
                                    <span className="v highlight" style={{ color: getScoreColor(sig.score) }}>
                                        {sig.score?.toFixed(1) || '0.0'}
                                    </span>
                                </div>
                                <div className="sig-status">
                                    <span className={`status-dot ${(sig.status || 'pending').toLowerCase()}`}></span>
                                    {sig.status}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {signals.length === 0 && (
                    <div className="empty-stream">Streaming liquidity data...</div>
                )}
            </div>
        );
    }

    return (
        <div className="live-stream-container">
            {/* ── Header ────────────────────────────────────────────── */}
            <div className="stream-header">
                <div className="stream-title">
                    <div className="live-indicator"></div>
                    Live Pipeline Signal Stream
                </div>
                <div style={{ fontSize: '0.7rem', color: scanTicker ? '#00e5ff' : '#666', fontFamily: 'Roboto Mono', transition: 'color 0.3s' }}>
                    {scanTicker ? (
                        <span>
                            <span style={{ fontWeight: 'bold' }}>SCAN:</span> {scanTicker.symbol}
                            <span style={{ margin: '0 8px', color: '#444' }}>|</span>
                            <span style={{ color: scanTicker.status === 'REJECTED' ? '#ff3366' : '#00ff88' }}>{scanTicker.status}</span>
                            <span style={{ margin: '0 8px', color: '#444' }}>|</span>
                            <span style={{ color: '#888' }}>{scanTicker.detail}</span>
                        </span>
                    ) : (
                        "OANDA INTELLIGENCE CORE: IDLE"
                    )}
                </div>
            </div>

            {/* ── Active Board (Top) ────────────────────────────────── */}
            <div className="active-board">
                <table className="board-table">
                    <thead>
                        <tr>
                            <th>ASSET</th>
                            <th>REGIME</th>
                            <th>STRUCT</th>
                            <th>DIRECTION</th>
                            <th>SCORE</th>
                            <th>STATUS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {signals.filter(s => s && (s.signalId || s.id)).map((sig, i) => {
                            const id = sig.signalId || sig.id;
                            return (
                                <tr key={id} className="board-row" onClick={() => onSignalSelect && onSignalSelect(sig)}>
                                    <td style={{ fontWeight: 'bold', color: '#e0e0e0' }}>{sig.symbol}</td>
                                    <td>
                                        <span className="pill-regime">{sig.regime || 'WAIT'}</span>
                                    </td>
                                    <td>
                                        <div className="heat-cell">
                                            <div className="heat-bar" style={{ background: sig.structure_score > 0 ? '#00e5ff' : '#333' }} title="Market Structure" />
                                            <div className="heat-bar" style={{ background: sig.volatility_score > 0 ? '#ffb400' : '#333' }} title="Volatility" />
                                            <div className="heat-bar" style={{ background: sig.liquidity_score > 0 ? '#aa00ff' : '#333' }} title="Liquidity" />
                                        </div>
                                    </td>
                                    <td className={sig.direction === 'BUY' ? 'text-buy' : (sig.direction === 'SELL' ? 'text-sell' : 'text-neutral')}>
                                        {sig.direction || 'WAIT'}
                                    </td>
                                    <td style={{ fontWeight: 'bold', fontFamily: 'Roboto Mono', color: getScoreColor(sig.score) }}>
                                        {sig.score?.toFixed(1) || '0.0'}
                                    </td>
                                    <td>
                                        <span className={`status-badge status-${(sig.status || 'pending').toLowerCase()}`}>
                                            {sig.status || 'PENDING'}
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                        {signals.length === 0 && (
                            <tr>
                                <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: '#444' }}>
                                    WAITING FOR DATA STREAM...
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* ── Event Tape (Bottom) ───────────────────────────────── */}
            <div className="event-tape">
                {tapeEvents.map(evt => (
                    <div key={evt.id} className="tape-entry">
                        <span className="tape-time">{formatTime(evt.time)}</span>
                        <span className="tape-symbol">{evt.symbol}</span>
                        <span className="tape-action">
                            {evt.type === 'ENTRY' && <span style={{ color: '#00e5ff' }}>ENTERED PIPELINE</span>}
                            {evt.type === 'SCORING' && <span>SCORE UPDATE</span>}
                            {evt.type === 'LIFECYCLE' && <span style={{ color: '#ffb400' }}>STATUS CHANGE</span>}
                        </span>
                        <span className="tape-detail" style={{ color: '#888' }}>
                            {evt.detail}
                        </span>
                    </div>
                ))}
                {tapeEvents.length === 0 && (
                    <div style={{ padding: '1rem', color: '#444', textAlign: 'center', fontStyle: 'italic' }}>
                        Processing events will appear here...
                    </div>
                )}
            </div>
        </div>
    );
}
