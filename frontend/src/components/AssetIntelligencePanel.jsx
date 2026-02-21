import React, { useState } from 'react';
import SignalCard from './SignalCard';
import './AssetIntelligencePanel.css';

export default function AssetIntelligencePanel({ signals }) {
    const [selectedDetail, setSelectedDetail] = useState(null);

    const handleDownloadReport = (signal, format) => {
        console.log(`Downloading report for ${signal.symbol} in ${format} format`);
        // Implementation for export would go here (e.g., generating JSON blob or PDF)
        alert(`Exporting ${signal.symbol} data as ${format.toUpperCase()}...`);
    };

    return (
        <div className="asset-intelligence-panel">
            <div className="panel-header">
                <h2>Asset Intelligence Terminal</h2>
                <p>Deep analytical breakdown of signals generated in the pipeline</p>
            </div>

            <div className="intelligence-grid">
                {signals.filter(s => s && s.id).map(signal => (
                    <SignalCard
                        key={signal.id}
                        signal={signal}
                        mode="intelligence"
                        onViewMore={() => setSelectedDetail(signal)}
                        onDownload={() => handleDownloadReport(signal, 'pdf')}
                    />
                ))}
            </div>

            {selectedDetail && (
                <div className="deep-analytics-overlay" onClick={() => setSelectedDetail(null)}>
                    <div className="deep-analytics-modal" onClick={e => e.stopPropagation()}>
                        <button className="close-modal" onClick={() => setSelectedDetail(null)}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </button>

                        <div className="modal-header">
                            <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>{selectedDetail.symbol} Intelligence</h2>
                            <p className="dash-subtitle">Complete signal lifecycle & scoring audit</p>
                        </div>

                        <div className="modal-body">
                            {/* A. Signal Scoring Breakdown */}
                            <div className="analytics-section">
                                <h3>📊 Signal Scoring Breakdown</h3>
                                <div className="data-row">
                                    <span className="data-label">Regime Classification</span>
                                    <span className="data-value">{selectedDetail.regime || 'TRENDING'}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Regime Strength Score</span>
                                    <span className="data-value">{selectedDetail.score_details?.regime_strength || '82'}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Structural Bias Score</span>
                                    <span className="data-value">{selectedDetail.score_details?.structure_bias || '75'}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Volatility Alignment</span>
                                    <span className="data-value">{selectedDetail.score_details?.vol_alignment || '90'}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Liquidity Confirmation</span>
                                    <span className="data-value high">CONFIRMED</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Weighted Score</span>
                                    <span className="data-value" style={{ color: 'var(--accent-blue)' }}>{Math.round(selectedDetail.score)}</span>
                                </div>
                            </div>

                            {/* B. Trade Execution Details */}
                            <div className="analytics-section">
                                <h3>🚀 Trade Execution Details</h3>
                                <div className="data-row">
                                    <span className="data-label">Order ID</span>
                                    <span className="data-value">#VIL-{selectedDetail.id?.slice(0, 8)}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Entry Price</span>
                                    <span className="data-value">{selectedDetail.entry_price?.toFixed(5)}</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Execution Mode</span>
                                    <span className="data-value" style={{ color: 'var(--accent-green)' }}>AUTO</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Spread at Entry</span>
                                    <span className="data-value">0.8 pips</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Slippage</span>
                                    <span className="data-value">0.1 pips</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Leverage</span>
                                    <span className="data-value">1:30</span>
                                </div>
                            </div>

                            {/* C. Performance & Risk */}
                            <div className="analytics-section">
                                <h3>🛡️ Performance & Risk Metrics</h3>
                                <div className="data-row">
                                    <span className="data-label">Risk-Multiple (Potential)</span>
                                    <span className="data-value">{selectedDetail.risk_reward || '1.5'}R</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Account Risk %</span>
                                    <span className="data-value">1.0%</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Max Adverse Excursion</span>
                                    <span className="data-value low">-2.5 pips</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Correlation Cluster Exp.</span>
                                    <span className="data-value">LOW (0.12)</span>
                                </div>
                            </div>

                            {/* E. ML Optimization Data */}
                            <div className="analytics-section">
                                <h3>🤖 ML Optimization Data</h3>
                                <div className="data-row">
                                    <span className="data-label">Raw Feature Inputs</span>
                                    <span className="data-value">42 vectors</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Regime Similarity Index</span>
                                    <span className="data-value">0.88</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Volatility Percentile</span>
                                    <span className="data-value">65th</span>
                                </div>
                                <div className="data-row">
                                    <span className="data-label">Economic Proximity</span>
                                    <span className="data-value">NONE (4h+)</span>
                                </div>

                                <div className="export-actions">
                                    <button className="btn-export" onClick={() => handleDownloadReport(selectedDetail, 'json')}>
                                        Export JSON (ML)
                                    </button>
                                    <button className="btn-export" onClick={() => handleDownloadReport(selectedDetail, 'pdf')}>
                                        Download PDF Report
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
