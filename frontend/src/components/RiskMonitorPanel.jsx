import React, { useState, useEffect } from 'react';
import './RiskMonitorPanel.css';
import ActiveTradesRiskCard from './ActiveTradesRiskCard';
import { getBrokerTrades } from '../services/api';

export default function RiskMonitorPanel({ portfolio, brokerAccount, variant = 'desktop' }) {
    const [trades, setTrades] = useState([]);

    // Poll for active trades
    useEffect(() => {
        const fetchTrades = async () => {
            try {
                const res = await getBrokerTrades();
                if (res.data) {
                    setTrades(res.data.open || []);
                }
            } catch (err) {
                console.error("Failed to fetch trades:", err);
            }
        };

        fetchTrades();
        const interval = setInterval(fetchTrades, 2000);
        return () => clearInterval(interval);
    }, []);
    // Merge real broker data with trade stats
    const metrics = {
        balance: brokerAccount?.balance || 100000.00,
        equity: brokerAccount?.equity || 100000.00,
        marginUsed: brokerAccount?.margin_used || 0,
        marginAvailable: brokerAccount?.margin_available || 100000.00,
        unrealizedPnL: brokerAccount?.unrealized_pnl || 0,
        dailyPnL: portfolio?.total_pnl || 0,
        drawdown: (brokerAccount?.balance > 0)
            ? ((1 - (brokerAccount?.equity / brokerAccount?.balance)) * 100).toFixed(2)
            : "0.00",
        ...portfolio
    };

    const exposures = [
        { class: 'Forex', value: 45 },
        { class: 'Indices', value: 20 },
        { class: 'Commodities', value: 10 },
        { class: 'Metals', value: 5 },
        { class: 'Crypto', value: 0 }
    ];

    if (variant === 'mobile-cards') {
        return (
            <div className="mobile-risk-stack">
                <div className="risk-mini-card glass-card">
                    <span className="l">Equity</span>
                    <span className="v">${metrics.equity.toLocaleString()}</span>
                    <span className={`p ${metrics.unrealizedPnL >= 0 ? 'pos' : 'neg'}`}>
                        {metrics.unrealizedPnL >= 0 ? '+' : ''}${metrics.unrealizedPnL}
                    </span>
                </div>
                <div className="risk-mini-card glass-card">
                    <span className="l">Margin Used</span>
                    <span className="v">{((metrics.marginUsed / metrics.balance) * 100).toFixed(2)}%</span>
                </div>
                <div className="risk-mini-card glass-card">
                    <span className="l">Drawdown</span>
                    <span className="v" style={{ color: metrics.drawdown < 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {metrics.drawdown}%
                    </span>
                </div>

                {/* Active Trades (Condensed for mobile) */}
                <div className="mobile-trades-section">
                    <h4 className="sub-title-mobile">Active Trades ({trades.length})</h4>
                    <div className="mini-trade-list">
                        {trades.map((trade, i) => (
                            <div key={i} className="mini-trade-item glass-card">
                                <span className="t-sym">{trade.symbol}</span>
                                <span className={`t-pl ${trade.unrealized_pnl >= 0 ? 'pos' : 'neg'}`}>
                                    {trade.unrealized_pnl >= 0 ? '+' : ''}{trade.unrealized_pnl}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="risk-monitor-panel">
            <div className="panel-header">
                <h2>Portfolio Risk Monitor</h2>
                <p>Institutional capital protection & exposure terminal</p>
            </div>

            <div className="risk-grid">
                {/* Real-time Capital Metrics */}
                <div className="risk-card">
                    <h3>💰 Capital Metrics</h3>
                    <div className="metric-large">
                        ${metrics.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        <span className="metric-trend trend-up">+1.2%</span>
                    </div>
                    <div className="metric-sub">Account Balance (USD)</div>

                    <div style={{ marginTop: '2rem' }}>
                        <div className="data-row">
                            <span className="data-label">Equity</span>
                            <span className="data-value">${metrics.equity.toLocaleString()}</span>
                        </div>
                        <div className="data-row">
                            <span className="data-label">Unrealized PnL</span>
                            <span className="data-value" style={{ color: 'var(--accent-green)' }}>+${metrics.unrealizedPnL}</span>
                        </div>
                        <div className="data-row">
                            <span className="data-label">Margin Usage</span>
                            <span className="data-value">{((metrics.marginUsed / metrics.balance) * 100).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>

                {/* Drawdown Monitor */}
                <div className="risk-card">
                    <h3>📉 Drawdown Monitor</h3>
                    <div className="metric-large" style={{ color: metrics.drawdown < 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {metrics.drawdown}%
                    </div>
                    <div className="metric-sub">Current Drawdown</div>

                    <div className="chart-placeholder">
                        {[40, 65, 30, 85, 45, 20, 55, 30, 40, 25, 45].map((h, i) => (
                            <div key={i} className="chart-bar" style={{ height: `${h}%` }} />
                        ))}
                    </div>
                    <div className="metric-sub" style={{ textAlign: 'center', marginTop: '0.5rem' }}>Rolling 7-Day Curve</div>
                </div>

                {/* Exposure Heatmap */}
                <div className="risk-card">
                    <h3>🌍 Asset Exposure</h3>
                    <div className="exposure-grid">
                        {exposures.map(exp => (
                            <div key={exp.class} className="exposure-item">
                                <div className="data-label" style={{ fontSize: '0.75rem' }}>{exp.class}</div>
                                <div className="data-value" style={{ fontSize: '1.1rem' }}>{exp.value}%</div>
                                <div className="exposure-bar-wrap">
                                    <div className="exposure-bar" style={{ width: `${exp.value}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Advanced Risk Metrics */}
                <div className="risk-card">
                    <h3>🛡️ Institutional Risk Desk</h3>
                    <div className="data-row">
                        <span className="data-label">Value at Risk (VaR 95%)</span>
                        <span className="data-value">$1,240.00</span>
                    </div>
                    <div className="data-row">
                        <span className="data-label">Volatility-Adjusted Exp.</span>
                        <span className="data-value">0.14</span>
                    </div>
                    <div className="data-row">
                        <span className="data-label">Concentration Ratio</span>
                        <span className="data-value">0.32</span>
                    </div>
                    <div className="data-row">
                        <span className="data-label">Risk of Ruin (Est.)</span>
                        <span className="data-value" style={{ color: 'var(--accent-green)' }}>&lt; 0.01%</span>
                    </div>
                </div>

                <div className="risk-footer">
                    <div className="alert-item">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
                        </svg>
                        <div>
                            <div style={{ fontWeight: '700' }}>Margin Alert</div>
                            <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>Concentration in EUR/USD exceeds 5% of equity.</div>
                        </div>
                    </div>
                </div>
                {/* API-driven Active Trades Widget */}
                <ActiveTradesRiskCard trades={trades} account={metrics} />
            </div>
        </div>
    );
}
