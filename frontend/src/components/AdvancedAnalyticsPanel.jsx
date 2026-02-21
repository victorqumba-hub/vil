import React from 'react';
import './AdvancedAnalyticsPanel.css';

export default function AdvancedAnalyticsPanel() {
    return (
        <div className="advanced-analytics-panel">
            <div className="panel-header">
                <h2>Advanced Market Analytics</h2>
                <p>System-wide intelligence, model calibration, and automation governance</p>
            </div>

            <div className="analytics-grid-main">
                {/* A. Regime Analytics */}
                <div className="analytics-card-small">
                    <h4>🌐 Regime Analytics</h4>
                    <div className="win-rate-ring">68%</div>
                    <div className="metric-sub" style={{ textAlign: 'center', marginBottom: '1.5rem' }}>Global Win Rate</div>

                    <div className="data-row">
                        <span className="data-label">Trending Win Rate</span>
                        <span className="data-value" style={{ color: 'var(--accent-green)' }}>74%</span>
                    </div>
                    <div className="data-row">
                        <span className="data-label">Mean Reversion WR</span>
                        <span className="data-value">52%</span>
                    </div>
                    <div className="data-row">
                        <span className="data-label">Regime Expectancy</span>
                        <span className="data-value">1.8R</span>
                    </div>
                </div>

                {/* B. Model Calibration */}
                <div className="analytics-card-small">
                    <h4>⚙️ Model Calibration</h4>
                    <div className="calibration-item">
                        <div className="cal-label-row"><span>Structural Bias Weight</span><span>45%</span></div>
                        <div className="cal-meter-bg"><div className="cal-meter-fill" style={{ width: '45%' }} /></div>
                    </div>
                    <div className="calibration-item">
                        <div className="cal-label-row"><span>Volatility Sensitivity</span><span>30%</span></div>
                        <div className="cal-meter-bg"><div className="cal-meter-fill" style={{ width: '30%' }} /></div>
                    </div>
                    <div className="calibration-item">
                        <div className="cal-label-row"><span>Liquidity Factor</span><span>25%</span></div>
                        <div className="cal-meter-bg"><div className="cal-meter-fill" style={{ width: '25%' }} /></div>
                    </div>
                    <div className="metric-sub" style={{ marginTop: '1rem' }}>Last adjusted: 2026-02-14 09:30</div>
                </div>

                {/* C. Automation Governance */}
                <div className="analytics-card-small">
                    <h4>🤖 Automation Governance</h4>
                    <div className="status-badge-row">
                        <span>Auto-Execution</span>
                        <div className="status-indicator"><span className="status-dot active" /> <span style={{ color: 'var(--accent-green)' }}>ENABLED</span></div>
                    </div>
                    <div className="status-badge-row">
                        <span>Risk Cap (Daily)</span>
                        <span>2.0% Equity</span>
                    </div>
                    <div className="status-badge-row">
                        <span>Max Open Trades</span>
                        <span>5</span>
                    </div>
                    <div className="status-badge-row">
                        <span>Circuit Breaker</span>
                        <span>ACTIVE (-3% Drawdown)</span>
                    </div>
                </div>

                {/* D. Data Integrity */}
                <div className="analytics-card-small">
                    <h4>📡 Data Integrity Panel</h4>
                    <div className="status-badge-row">
                        <span>OANDA Connection</span>
                        <div className="status-indicator"><span className="status-dot active" /> <span>STABLE</span></div>
                    </div>
                    <div className="status-badge-row">
                        <span>WebSocket Latency</span>
                        <span style={{ color: 'var(--accent-green)' }}>120ms</span>
                    </div>
                    <div className="status-badge-row">
                        <span>Market Feed Uptime</span>
                        <span>99.98%</span>
                    </div>
                    <div className="status-badge-row">
                        <span>Signal Lag (Avg)</span>
                        <span>450ms</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
