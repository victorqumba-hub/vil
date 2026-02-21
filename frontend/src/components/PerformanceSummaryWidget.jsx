import React from 'react';

export default function PerformanceSummaryWidget({ signals }) {
    // Calculate metrics from signals array
    const today = new Date().toISOString().split('T')[0];
    const signalsToday = signals.filter(s => s.timestamp.startsWith(today));
    const activeSignals = signals.filter(s => s.status === 'ACTIVE').length;

    const succeeded = signals.filter(s => s.status === 'SUCCEEDED').length;
    const failed = signals.filter(s => s.status === 'FAILED').length;
    const winRate = (succeeded + failed) > 0
        ? ((succeeded / (succeeded + failed)) * 100).toFixed(1)
        : '0.0';

    // Mock average R multiple for now (in a real system, this would come from closed trades)
    const avgR = 1.8;

    const regimeDistribution = signals.reduce((acc, s) => {
        acc[s.regime] = (acc[s.regime] || 0) + 1;
        return acc;
    }, {});

    return (
        <div className="performance-summary">
            <div className="metric-card">
                <div className="metric-label">Today's Volume</div>
                <div className="metric-value">{signalsToday.length}</div>
            </div>
            <div className="metric-card">
                <div className="metric-label">Active Monitor</div>
                <div className="metric-value" style={{ color: '#00e5ff' }}>{activeSignals}</div>
            </div>
            <div className="metric-card">
                <div className="metric-label">Success Rate (7D)</div>
                <div className="metric-value positive">{winRate}%</div>
            </div>
            <div className="metric-card">
                <div className="metric-label">Avg R Multiple</div>
                <div className="metric-value">{avgR}R</div>
            </div>
        </div>
    );
}
