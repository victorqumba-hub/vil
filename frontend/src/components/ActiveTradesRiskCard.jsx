import React, { useState, useEffect } from 'react';
import './ActiveTradesRiskCard.css';

/**
 * ActiveTradesRiskCard - Institutional Risk Intelligence Widget
 * Monitors open positions, margin exposure, and progress toward TP/SL.
 */
export default function ActiveTradesRiskCard({ trades = [], account = {} }) {
    const [debugMode, setDebugMode] = useState(false);
    const [displayTrades, setDisplayTrades] = useState([]);

    // ── Fake Data Generator for Debugging ─────────────────────────────
    const FAKE_TRADES = [
        {
            broker_order_id: 'DEBUG-001',
            symbol: 'EUR/USD',
            direction: 'BUY',
            units: 100000,
            lotSize: '1.00',
            entry_price: 1.08500,
            current_price: 1.08920,
            stop_loss: 1.08200,
            take_profit: 1.09500,
            unrealized_pnl: 420.00,
            margin_used: 2000.00,
            open_time: '2023-10-27T10:00:00Z',
            status: 'OPEN',
            risk: { spread: 'PRO', correlation: 'HIGH' }
        },
        {
            broker_order_id: 'DEBUG-002',
            symbol: 'XAU/USD',
            direction: 'SELL',
            units: 10,
            lotSize: '0.10',
            entry_price: 2050.00,
            current_price: 2055.00,
            stop_loss: 2060.00,
            take_profit: 2020.00,
            unrealized_pnl: -500.00,
            margin_used: 1500.00,
            open_time: '2023-10-27T11:30:00Z',
            status: 'OPEN',
            risk: { spread: 'OK', correlation: 'MED' }
        },
        {
            broker_order_id: 'DEBUG-003',
            symbol: 'GBP/JPY',
            direction: 'BUY',
            units: 50000,
            lotSize: '0.50',
            entry_price: 182.500,
            current_price: 182.900,
            stop_loss: 181.500,
            take_profit: 184.000,
            unrealized_pnl: 280.00,
            margin_used: 1000.00,
            open_time: '2023-10-27T12:00:00Z',
            status: 'OPEN',
            risk: { spread: 'OK', correlation: 'LOW' }
        }
    ];

    useEffect(() => {
        if (debugMode) {
            setDisplayTrades(FAKE_TRADES);
        } else {
            // Process real trades
            const processed = trades.map(t => ({
                ...t,
                lotSize: (Math.abs(t.units) / 100000).toFixed(2), // Simplify lot calc
                current_price: t.current_price || t.entry_price, // Fallback if no live feed yet
            }));
            setDisplayTrades(processed);
        }
    }, [trades, debugMode]);

    // ── Helper Logic ───────────────────────────────────────────────

    const calculateProgress = (trade) => {
        if (!trade.take_profit || !trade.stop_loss) return { pct: 0, label: 'N/A' };

        const entry = trade.entry_price;
        const current = trade.current_price;
        const tp = trade.take_profit;

        // Distance to TP
        let totalStats = 0;
        let covered = 0;

        if (trade.direction === 'BUY') {
            totalStats = tp - entry;
            covered = current - entry;
        } else {
            totalStats = entry - tp;
            covered = entry - current;
        }

        if (totalStats === 0) return { pct: 0, label: '0%' };

        let pct = (covered / totalStats) * 100;
        pct = Math.min(Math.max(pct, -20), 120); // Clamp for display

        return { pct, label: `${Math.round(pct)}%` };
    };

    const getRMultiple = (trade) => {
        if (!trade.stop_loss) return '0.0R';
        const risk = Math.abs(trade.entry_price - trade.stop_loss);
        if (risk === 0) return '0.0R';

        let diff = 0;
        if (trade.direction === 'BUY') diff = trade.current_price - trade.entry_price;
        else diff = trade.entry_price - trade.current_price;

        return `${(diff / risk).toFixed(1)}R`;
    };

    // ── Metrics Aggregation ────────────────────────────────────────

    const totalMargin = displayTrades.reduce((acc, t) => acc + (t.margin_used || 0), 0);
    const count = displayTrades.length;
    const totalPnL = displayTrades.reduce((acc, t) => acc + (t.unrealized_pnl || 0), 0);
    const balance = account.balance || 100000;
    const marginPct = (totalMargin / balance) * 100;

    // AI Insight Logic (Simple rule-based for now)
    const getInsight = () => {
        if (marginPct > 10) return { type: 'WARN', msg: 'High margin utilization. Monitor leverage.' };
        if (count > 5) return { type: 'INFO', msg: 'High number of open positions. Grid risk elevated.' };
        const exposure = displayTrades.reduce((acc, t) => {
            const asset = t.symbol.split('/')[0]; // e.g., EUR
            acc[asset] = (acc[asset] || 0) + 1;
            return acc;
        }, {});
        const maxExp = Math.max(...Object.values(exposure));
        if (maxExp > 2) return { type: 'WARN', msg: 'Concentration risk detected in single asset class.' };
        return { type: 'OK', msg: 'Portfolio risk parameters within normal limits.' };
    };

    const insight = getInsight();

    // ── Render ─────────────────────────────────────────────────────

    return (
        <div className="active-trades-card">
            <div className="at-header">
                <div className="at-title">
                    <div className="live-dot" title="Live connection active" />
                    Active Trades Risk
                    {debugMode && <span style={{ fontSize: '0.7rem', color: 'orange' }}>(DEBUG)</span>}
                </div>
                <div className="at-header-metrics">
                    <div className="at-metric">
                        <span className="at-metric-label">Open</span>
                        <span className="at-metric-value">{count}</span>
                    </div>
                    <div className="at-metric">
                        <span className="at-metric-label">Margin</span>
                        <span className="at-metric-value">{marginPct.toFixed(1)}%</span>
                    </div>
                    <div className="at-metric">
                        <span className="at-metric-label">Float P/L</span>
                        <span className={`at-metric-value ${totalPnL >= 0 ? 'val-pos' : 'val-neg'}`}>
                            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>

            {count === 0 ? (
                <div className="at-empty">
                    No active trades. Portfolio is flat.
                </div>
            ) : (
                <div className="at-table-container">
                    <table className="at-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Dir</th>
                                <th>Size</th>
                                <th>Entry</th>
                                <th>Current</th>
                                <th>Progress / TP</th>
                                <th>R-Mult</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayTrades.map(trade => {
                                const prog = calculateProgress(trade);
                                const rMult = getRMultiple(trade);
                                const isProfit = trade.unrealized_pnl >= 0;

                                return (
                                    <tr key={trade.broker_order_id} className="at-row">
                                        <td data-label="Asset" className="cell-asset">
                                            {trade.symbol}
                                        </td>
                                        <td data-label="Dir">
                                            <span className={`cell-dir ${trade.direction === 'BUY' ? 'dir-buy' : 'dir-sell'}`}>
                                                {trade.direction === 'BUY' ? '▲ BUY' : '▼ SELL'}
                                            </span>
                                        </td>
                                        <td data-label="Size" className="cell-price">{trade.lotSize}</td>
                                        <td data-label="Entry" className="cell-price">{trade.entry_price?.toFixed(5)}</td>
                                        <td data-label="Current" className="cell-price">{trade.current_price?.toFixed(5)}</td>
                                        <td data-label="Progress" className="progress-cell">
                                            <div className="progress-container">
                                                <div className="progress-bar-bg">
                                                    <div
                                                        className={`progress-bar-fill ${isProfit ? 'prog-pos' : 'prog-neg'}`}
                                                        style={{ width: `${Math.max(0, prog.pct)}%` }}
                                                    />
                                                    <div className="tp-marker" title="Take Profit" />
                                                </div>
                                                <div className="progress-labels">
                                                    <span className="prog-pct">{prog.label}</span>
                                                    <span className="prog-limit">{trade.take_profit?.toFixed(5)}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td data-label="R-Mult" className={`prog-r ${isProfit ? 'val-pos' : 'val-neg'}`}>
                                            {rMult}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="at-footer">
                <div className="agg-metrics">
                    <div className="agg-item">
                        <span className="agg-label">Total Risk</span>
                        <span className="agg-val">$240.50</span>
                    </div>
                    <div className="agg-item">
                        <span className="agg-label">Net Exp</span>
                        <span className="agg-val">1.4 Lots</span>
                    </div>
                </div>

                <div className="smart-insight">
                    <div className="insight-header">
                        ⚡ AI Risk Insight
                    </div>
                    <div className="insight-text">
                        {insight.msg}
                    </div>
                </div>
            </div>

            {/* Debug Toggle */}
            <div className="at-debug-ctrl">
                <input
                    type="checkbox"
                    checked={debugMode}
                    onChange={e => setDebugMode(e.target.checked)}
                />
            </div>
        </div>
    );
}
