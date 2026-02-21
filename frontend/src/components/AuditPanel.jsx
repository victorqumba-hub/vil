import React from 'react';
import './AuditPanel.css';
import RegimePerformanceAttributionCard from './RegimePerformanceAttributionCard';

export default function AuditPanel() {
    const auditLogs = [
        { id: 1, time: '18:02:15', type: 'EXECUTION', title: 'Auto-Trade Executed', desc: 'EUR/USD BUY @ 1.08452 - Order #88219' },
        { id: 2, time: '18:00:04', type: 'SIGNAL', title: 'Signal Score Upgrade', desc: 'GBP/JPY score shifted from 82 to 89 (Regime Alignment)' },
        { id: 3, time: '17:58:30', type: 'SYSTEM', title: 'OANDA Pipeline Scan', desc: 'Successfully processed 12 instruments in 0.8s' },
        { id: 4, time: '17:55:12', type: 'ERROR', title: 'API Connection Latency', desc: 'OANDA REST API responded in 1200ms (Above Threshold)', status: 'error' },
        { id: 5, time: '17:50:00', type: 'SIGNAL', title: 'Signal Generated', desc: 'New AUD/USD BUY signal identified in H1 Trend Regime' },
    ];

    const scoreComparisons = [
        { symbol: 'EUR/USD', gen: 78, entry: 82, current: 85, shift: '+7' },
        { symbol: 'GBP/JPY', gen: 85, entry: 89, current: 87, shift: '+2' },
        { symbol: 'XAU/USD', gen: 92, entry: 90, current: 88, shift: '-4' },
        { symbol: 'USD/CAD', gen: 70, entry: 72, current: 75, shift: '+5' },
    ];

    return (
        <div className="audit-panel">
            <div className="panel-header">
                <h2>Score Comparison & Audit</h2>
                <p>Full transparency engine for signal evolution and system events</p>
            </div>

            <div className="audit-grid">
                {/* Score Audit Record */}
                <div className="audit-card">
                    <h3>⚖️ Score Evolution Audit</h3>
                    <table className="audit-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Generated</th>
                                <th>At Entry</th>
                                <th>Current</th>
                                <th>Drift</th>
                            </tr>
                        </thead>
                        <tbody>
                            {scoreComparisons.map(row => (
                                <tr key={row.symbol}>
                                    <td style={{ fontWeight: 700 }}>{row.symbol}</td>
                                    <td>{row.gen}</td>
                                    <td>{row.entry}</td>
                                    <td style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{row.current}</td>
                                    <td className={row.shift.startsWith('+') ? 'score-up' : 'score-down'}>
                                        {row.shift}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* System Event Logs */}
                <div className="audit-card">
                    <h3>📜 Institutional Event Log</h3>
                    <div className="audit-timeline">
                        {auditLogs.map(log => (
                            <div key={log.id} className={`timeline-item ${log.status === 'error' ? 'error' : ''}`}>
                                <div className="timeline-time">{log.time}</div>
                                <div className="timeline-content">
                                    <div className="timeline-title">{log.title}</div>
                                    <div className="timeline-desc">{log.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Regime Performance Attribution Intelligence ── */}
            <RegimePerformanceAttributionCard />
        </div>
    );
}
