import React, { useEffect, useState } from 'react';
import './OandaScanner.css';

const OandaScanner = ({ pipelineStatus }) => {
    const [elapsed, setElapsed] = useState(0);

    useEffect(() => {
        if (!pipelineStatus?.last_run_time) return;

        const interval = setInterval(() => {
            const start = new Date(pipelineStatus.last_run_time).getTime();
            const now = new Date().getTime();
            setElapsed(Math.floor((now - start) / 1000));
        }, 1000);

        return () => clearInterval(interval);
    }, [pipelineStatus?.last_run_time]);

    const getStatusColor = () => {
        switch (pipelineStatus?.status) {
            case 'success': return '#00ff88';
            case 'running': return '#00d4ff';
            case 'error': return '#ff4444';
            default: return '#888';
        }
    };

    const formatTime = (isoString) => {
        if (!isoString) return 'Never';
        return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    return (
        <div className="oanda-scanner glass-card">
            <div className="scanner-header">
                <div className="status-indicator">
                    <div className={`status-pulse ${pipelineStatus?.status}`} style={{ backgroundColor: getStatusColor() }}></div>
                    <h3>OANDA Pipeline Scan</h3>
                </div>
                <span className="refresh-rate">2m Cycle</span>
            </div>

            <div className="scanner-content">
                <div className="scan-item">
                    <span className="label">Current Status:</span>
                    <span className={`status-text ${pipelineStatus?.status}`}>
                        {pipelineStatus?.status?.toUpperCase() || 'IDLE'}
                    </span>
                </div>

                <div className="scan-item">
                    <span className="label">Last Success:</span>
                    <span className="value success-text">{formatTime(pipelineStatus?.last_success_time)}</span>
                </div>

                <div className="scan-item">
                    <span className="label">Last Failure:</span>
                    <span className="value error-text">{formatTime(pipelineStatus?.last_failure_time)}</span>
                </div>

                {pipelineStatus?.status === 'running' && (
                    <div className="scanning-animation">
                        <div className="scan-bar"></div>
                        <span className="scan-msg">{pipelineStatus?.message}</span>
                    </div>
                )}

                {pipelineStatus?.status === 'error' && (
                    <div className="error-alert">
                        <span className="error-icon">⚠️</span>
                        <div className="error-details">
                            <p className="error-msg">{pipelineStatus?.message}</p>
                            {pipelineStatus?.last_error && <p className="error-debug">{pipelineStatus.last_error}</p>}
                        </div>
                    </div>
                )}

                {pipelineStatus?.processed_symbols?.length > 0 && (
                    <div className="processed-list">
                        <span className="label">Active Ingestion:</span>
                        <div className="symbol-chips">
                            {pipelineStatus.processed_symbols.map(sym => (
                                <span key={sym} className="symbol-chip">{sym}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="scanner-footer">
                <div className="footer-auth">
                    <span className="auth-badge">AUTHENTICATED</span>
                    <span className="data-source">Source: OANDA Live (v20)</span>
                </div>
                <span className="elapsed">{pipelineStatus?.status === 'running' ? `In progress for ${elapsed}s` : `Last update ${elapsed}s ago`}</span>
            </div>
        </div>
    );
};

export default OandaScanner;
