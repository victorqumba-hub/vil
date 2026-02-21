import React, { useState, useEffect } from 'react';
import { getIntelligenceReports, getHistoricalSignals, getForensicAnalysis } from '../services/api';
import GlassCard from './GlassCard';
import './SignalIntelligenceLab.css';

const SignalIntelligenceLab = () => {
    const [reports, setReports] = useState([]);
    const [recentSignals, setRecentSignals] = useState([]);
    const [selectedSignal, setSelectedSignal] = useState(null);
    const [forensicData, setForensicData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLabData();
    }, []);

    const fetchLabData = async () => {
        try {
            setLoading(true);
            const [reportRes, signalRes] = await Promise.all([
                getIntelligenceReports(5),
                getHistoricalSignals({ limit: 10, terminal: true })
            ]);
            setReports(reportRes.data);
            setRecentSignals(signalRes.data.signals || []);
        } catch (err) {
            console.error('Failed to fetch Lab data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSignalClick = async (signal) => {
        setSelectedSignal(signal);
        setForensicData(null);
        try {
            const res = await getForensicAnalysis(signal.id);
            setForensicData(res.data);
        } catch (err) {
            console.error('Failed to fetch forensic analysis:', err);
        }
    };

    if (loading) return <div className="lab-loading">Initializing Intelligence Core...</div>;

    return (
        <div className="signal-intelligence-lab">
            <header className="lab-header">
                <h2 className="lab-title">Signal Intelligence Lab <span className="v-tag">v3.0</span></h2>
                <p className="lab-subtitle">Forensic causality, engine self-critique, and batch intelligence.</p>
            </header>

            <div className="lab-grid">
                {/* Section 1: Intelligence Reports */}
                <div className="lab-section reports-section">
                    <h3 className="section-title">Automated Intelligence Reports</h3>
                    <div className="reports-list">
                        {reports.length > 0 ? reports.map(report => (
                            <div key={report.id} className="intelligence-report-card glass-card">
                                <div className="report-header">
                                    <span className="report-date">{new Date(report.created_at).toLocaleDateString()}</span>
                                    <span className="report-tag">BATCH {report.signal_count}</span>
                                </div>
                                <p className="report-summary">{report.executive_summary}</p>
                                <div className="report-stats">
                                    <div className="stat">
                                        <span className="stat-label">Expectancy</span>
                                        <span className={`stat-value ${report.expectancy >= 0 ? 'pos' : 'neg'}`}>
                                            {report.expectancy?.toFixed(2)}R
                                        </span>
                                    </div>
                                    <button className="btn-text">View Full Analysis ➔</button>
                                </div>
                            </div>
                        )) : (
                            <div className="empty-state">No batch reports generated. Accumulating signal data (min. 50)...</div>
                        )}
                    </div>
                </div>

                {/* Section 2: Recent Terminal Signals */}
                <div className="lab-section forensic-queue">
                    <h3 className="section-title">Forensic Signal Queue</h3>
                    <div className="signals-table-wrapper glass-card">
                        <table className="signals-table">
                            <thead>
                                <tr>
                                    <th>Asset</th>
                                    <th>Outcome</th>
                                    <th>R multiple</th>
                                    <th>Quality</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentSignals.map(sig => (
                                    <tr key={sig.id} className={selectedSignal?.id === sig.id ? 'active' : ''}>
                                        <td>
                                            <div className="asset-info">
                                                <span className="symbol">{sig.symbol}</span>
                                                <span className="direction-tag">{sig.direction}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`status-pill ${sig.status.toLowerCase()}`}>{sig.status}</span>
                                        </td>
                                        <td>
                                            <span className={`r-val ${sig.r_multiple_achieved >= 0 ? 'pos' : 'neg'}`}>
                                                {sig.r_multiple_achieved ? sig.r_multiple_achieved.toFixed(2) + 'R' : '--'}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="quality-bar">
                                                <div className="fill" style={{ width: `${sig.score}%` }}></div>
                                            </div>
                                        </td>
                                        <td>
                                            <button className="btn-sm btn-outline" onClick={() => handleSignalClick(sig)}>Analyze</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Forensic Detail View */}
            {selectedSignal && (
                <div className="forensic-detail-view animate-in">
                    <div className="view-header">
                        <h3>Forensic Trace: {selectedSignal.symbol}</h3>
                        <button className="btn-close" onClick={() => setSelectedSignal(null)}>&times;</button>
                    </div>

                    <div className="forensic-grid">
                        <div className="forensic-main">
                            <h4 className="sub-title">Causality Analysis</h4>
                            <div className="causality-box glass-card">
                                {forensicData?.causality_summary || "Performing ML causality trace..."}
                            </div>

                            <h4 className="sub-title">Engine Self-Critique</h4>
                            <div className="critique-box glass-card">
                                {forensicData?.engine_critique || "Awaiting engine critique payload..."}
                            </div>
                        </div>

                        <div className="forensic-sidebar">
                            <h4 className="sub-title">Outcome Metrics</h4>
                            <div className="metrics-grid">
                                <div className="metric-box">
                                    <label>MFE</label>
                                    <span>{selectedSignal.mfe?.toFixed(5) || '--'}</span>
                                </div>
                                <div className="metric-box">
                                    <label>MAE</label>
                                    <span>{selectedSignal.mae?.toFixed(5) || '--'}</span>
                                </div>
                                <div className="metric-box">
                                    <label>Slippage</label>
                                    <span>{selectedSignal.slippage?.toFixed(5) || '0.000'}</span>
                                </div>
                                <div className="metric-box">
                                    <label>Regime Shift</label>
                                    <span>{selectedSignal.regime_shift_during_trade ? 'YES' : 'NO'}</span>
                                </div>
                            </div>

                            <h4 className="sub-title">Engine Bias Adjustments</h4>
                            <div className="adjustments-box highlight-card">
                                {forensicData?.suggested_adjustments || "No structural bias detected."}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SignalIntelligenceLab;
