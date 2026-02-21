import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './HistoricalLabPanel.css';

export default function HistoricalLabPanel() {
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedSignal, setSelectedSignal] = useState(null);
    const [forensicData, setForensicData] = useState(null);
    const [filters, setFilters] = useState({
        asset: '',
        regime: '',
        status: '',
        minScore: '',
        dateRange: '7d'
    });

    useEffect(() => {
        fetchHistoricalSignals();
    }, [filters]);

    const fetchHistoricalSignals = async () => {
        setLoading(true);
        try {
            const params = {
                asset_class: filters.asset || undefined,
                status: filters.status || undefined,
                min_score: filters.minScore || undefined,
                limit: 50
            };
            const response = await api.get(`/api/signals/history`, { params });
            setSignals(response.data);
        } catch (error) {
            console.error("Error fetching historical signals:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchForensic = async (signalId) => {
        try {
            const response = await api.get(`/api/signals/${signalId}/forensic`);
            setForensicData(response.data);
        } catch (error) {
            console.error("Error fetching forensic data:", error);
        }
    };

    const handleSignalClick = (signal) => {
        setSelectedSignal(signal);
        fetchForensic(signal.id);
    };

    return (
        <div className="historical-lab-panel">
            <div className="panel-header">
                <div className="header-info">
                    <h1>Forensic Intelligence Lab</h1>
                    <p className="subtitle">Quantitative Analysis & ML Dataset Research Terminal</p>
                </div>
                <div className="lab-actions">
                    <button className="btn-secondary">Export ML Dataset (JSON)</button>
                    <button className="btn-primary">Batch Export Labels</button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="lab-controls">
                <div className="filter-group">
                    <label>Asset Universe</label>
                    <select
                        className="filter-input"
                        value={filters.asset}
                        onChange={(e) => setFilters({ ...filters, asset: e.target.value })}
                    >
                        <option value="">All Assets</option>
                        <option value="forex">Forex</option>
                        <option value="crypto">Crypto</option>
                        <option value="index">Indices</option>
                        <option value="metal">Metals</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>Regime State</label>
                    <select
                        className="filter-input"
                        value={filters.regime}
                        onChange={(e) => setFilters({ ...filters, regime: e.target.value })}
                    >
                        <option value="">Any Regime</option>
                        <option value="TRENDING">Trending</option>
                        <option value="RANGING">Ranging</option>
                        <option value="HIGH_VOLATILITY">High Volatilty</option>
                        <option value="EVENT_RISK">Event Risk</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>Status</label>
                    <select
                        className="filter-input"
                        value={filters.status}
                        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                    >
                        <option value="">All Statuses</option>
                        <option value="SUCCESS">Success</option>
                        <option value="FAILED">Failed</option>
                        <option value="EXPIRED">Expired</option>
                        <option value="DROPPED">Dropped</option>
                        <option value="ACTIVE">Active</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>Min Score</label>
                    <input
                        type="number"
                        className="filter-input"
                        placeholder="e.g. 70"
                        value={filters.minScore}
                        onChange={(e) => setFilters({ ...filters, minScore: e.target.value })}
                    />
                </div>

                <div className="filter-group">
                    <label>Lookback</label>
                    <select
                        className="filter-input"
                        value={filters.dateRange}
                        onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                    >
                        <option value="24h">Today</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="all">All Time</option>
                    </select>
                </div>
            </div>

            {/* Historical Table */}
            <div className="forensic-table-container">
                {loading ? (
                    <div className="loader-center">Scanning Historical Datasets...</div>
                ) : (
                    <table className="forensic-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Symbol</th>
                                <th>Dir</th>
                                <th>Regime</th>
                                <th>Init Score</th>
                                <th>Final Status</th>
                                <th>R:R</th>
                                <th>Version</th>
                            </tr>
                        </thead>
                        <tbody>
                            {signals.map(s => (
                                <tr key={s.id} onClick={() => handleSignalClick(s)}>
                                    <td>{new Date(s.timestamp).toLocaleString()}</td>
                                    <td className="symbol-cell">{s.symbol}</td>
                                    <td className={s.direction === 'BUY' ? 'text-success' : 'text-danger'}>
                                        {s.direction}
                                    </td>
                                    <td>
                                        <span className="regime-tag">{s.regime}</span>
                                    </td>
                                    <td>
                                        <div className="score-mini">
                                            <span className="score-val">{s.score.toFixed(1)}</span>
                                            <div className="score-bar-bg">
                                                <div className="score-bar-fill" style={{ width: `${s.score}%`, background: s.score > 70 ? 'var(--status-success)' : 'var(--accent-primary)' }}></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`status-badge status-${s.status?.toLowerCase()}`}>
                                            {s.status}
                                        </span>
                                    </td>
                                    <td>{s.risk_reward.toFixed(2)}</td>
                                    <td>v{s.version || 1}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Forensic Detail Modal */}
            {selectedSignal && forensicData && (
                <div className="forensic-detail-overlay" onClick={() => setSelectedSignal(null)}>
                    <div className="forensic-detail-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h2>{selectedSignal.symbol} Forensic Analysis</h2>
                                <p className="subtitle">ID: {selectedSignal.id}</p>
                            </div>
                            <button className="close-btn" onClick={() => setSelectedSignal(null)}>&times;</button>
                        </div>
                        <div className="modal-content">
                            <div className="modal-main">
                                <div className="lab-widget">
                                    <h3 className="widget-title">Full Audit Lineage</h3>
                                    <div className="audit-timeline">
                                        {forensicData.audits?.map((event, idx) => (
                                            <div key={idx} className="audit-event">
                                                <span className="event-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
                                                <span className="event-label">{event.previous_state || 'START'} &rarr; {event.new_state}</span>
                                                <span className="event-reason">({event.reason})</span>
                                                <span className="event-trigger">via {event.triggered_by}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="lab-widget" style={{ marginTop: '1.5rem' }}>
                                    <h3 className="widget-title">ML Feature Snapshot at Creation</h3>
                                    <div className="feature-grid">
                                        {forensicData.features && Object.entries(forensicData.features).map(([key, val]) => (
                                            key !== 'id' && key !== 'signal_id' && (
                                                <div key={key} className="feature-item">
                                                    <span className="feature-label">{key.replace(/_/g, ' ')}</span>
                                                    <span className="feature-value">{typeof val === 'number' ? val.toFixed(4) : val}</span>
                                                </div>
                                            )
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <div className="modal-sidebar">
                                <div className="lab-widget status-summary">
                                    <h3 className="widget-title">Final Outcome Metrics</h3>
                                    <div className="metric-row">
                                        <span>Terminal State</span>
                                        <span className={`status-badge status-${selectedSignal.status?.toLowerCase()}`}>{selectedSignal.status}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span>R-Multiple</span>
                                        <span className={selectedSignal.status === 'SUCCESS' ? 'text-success' : 'text-danger'}>
                                            {selectedSignal.status === 'SUCCESS' ? `+${selectedSignal.risk_reward.toFixed(2)}` : (selectedSignal.status === 'FAILED' ? '-1.00' : '0.00')}
                                        </span>
                                    </div>
                                    <div className="metric-row">
                                        <span>Score Decay</span>
                                        <span className="text-muted">{selectedSignal.decay_rate ? `${selectedSignal.decay_rate.toFixed(2)} pts/hr` : 'N/A'}</span>
                                    </div>
                                </div>
                                <div className="lab-widget regime-context" style={{ marginTop: '1.5rem' }}>
                                    <h3 className="widget-title">Regime Context</h3>
                                    <div className="regime-snapshot">
                                        <div className="regime-val">{selectedSignal.regime}</div>
                                        <div className="regime-desc">Regime stability at creation was high. No significant shifts detected during the entry window.</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
