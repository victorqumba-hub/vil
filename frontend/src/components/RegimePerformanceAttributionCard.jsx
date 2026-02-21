import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getRegimeAttribution } from '../services/api';
import './RegimePerformanceAttributionCard.css';

const REGIME_COLORS = {
    TRENDING_BULLISH: '#10b981',
    TRENDING_BEARISH: '#ef4444',
    RANGING_WIDE: '#f59e0b',
    RANGING_NARROW: '#6366f1',
    VOLATILITY_EXPANSION: '#8b5cf6',
    HIGH_VOLATILITY: '#ec4899',
    UNSTABLE: '#f97316',
    EVENT_RISK: '#dc2626',
    LOW_ACTIVITY: '#6b7280',
    TRENDING: '#22c55e',
    RANGING: '#eab308',
    UNKNOWN: '#4b5563',
};

const REGIME_LABELS = {
    TRENDING_BULLISH: 'Trend ↑',
    TRENDING_BEARISH: 'Trend ↓',
    RANGING_WIDE: 'Range W',
    RANGING_NARROW: 'Range N',
    VOLATILITY_EXPANSION: 'Vol Exp',
    HIGH_VOLATILITY: 'High Vol',
    UNSTABLE: 'Unstable',
    EVENT_RISK: 'Event',
    LOW_ACTIVITY: 'Low Act',
    TRENDING: 'Trending',
    RANGING: 'Ranging',
    UNKNOWN: '—',
};

function RegimeBadge({ regime }) {
    const color = REGIME_COLORS[regime] || REGIME_COLORS.UNKNOWN;
    const label = REGIME_LABELS[regime] || regime || '—';
    return (
        <span className="rpa-regime-badge" style={{ borderColor: color, color }}>
            {label}
        </span>
    );
}

function StatBadge({ label, value, accent }) {
    return (
        <div className={`rpa-stat-badge ${accent || ''}`}>
            <span className="rpa-stat-val">{value}</span>
            <span className="rpa-stat-label">{label}</span>
        </div>
    );
}

export default function RegimePerformanceAttributionCard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedPanel, setExpandedPanel] = useState('forensic');

    // Filters
    const [filters, setFilters] = useState({
        limit: 50,
        asset_class: '',
        regime_type: '',
        min_confidence: '',
        regime_flip_only: false,
    });

    const [debouncedFilters, setDebouncedFilters] = useState(filters);

    // Debounce filter changes
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedFilters(filters), 400);
        return () => clearTimeout(timer);
    }, [filters]);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = {};
            if (debouncedFilters.limit) params.limit = debouncedFilters.limit;
            if (debouncedFilters.asset_class) params.asset_class = debouncedFilters.asset_class;
            if (debouncedFilters.regime_type) params.regime_type = debouncedFilters.regime_type;
            if (debouncedFilters.min_confidence) params.min_confidence = parseFloat(debouncedFilters.min_confidence);
            if (debouncedFilters.regime_flip_only) params.regime_flip_only = true;

            const res = await getRegimeAttribution(params);
            setData(res.data);
        } catch (err) {
            console.error('[RegimeAttribution] Failed to fetch:', err);
            setError('Failed to load regime attribution data');
        } finally {
            setLoading(false);
        }
    }, [debouncedFilters]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const header = data?.header || {};
    const winners = data?.winners || [];
    const losers = data?.losers || [];
    const matrix = data?.comparison_matrix || [];
    const forensic = data?.forensic_analysis || {};
    const regimeBreakdown = data?.regime_breakdown || {};

    // Panel toggle
    const togglePanel = (id) => {
        setExpandedPanel(prev => prev === id ? null : id);
    };

    return (
        <div className="rpa-card">
            {/* ── Header ── */}
            <div className="rpa-header">
                <div className="rpa-title-block">
                    <h3 className="rpa-title">
                        <span className="rpa-icon">🔬</span>
                        Signal Regime Attribution Analysis
                    </h3>
                    <p className="rpa-subtitle">
                        Last {header.total_signals || 0} Signals | Regime-Based Performance Intelligence
                    </p>
                </div>
                <button className="rpa-refresh-btn" onClick={fetchData} disabled={loading}>
                    {loading ? '⟳' : '↻'} Refresh
                </button>
            </div>

            {/* ── Filters ── */}
            <div className="rpa-filters">
                <select
                    value={filters.asset_class}
                    onChange={e => handleFilterChange('asset_class', e.target.value)}
                    className="rpa-filter-select"
                >
                    <option value="">All Assets</option>
                    <option value="forex">Forex</option>
                    <option value="index">Indices</option>
                    <option value="commodity">Commodities</option>
                    <option value="metal">Metals</option>
                    <option value="crypto">Crypto</option>
                </select>

                <select
                    value={filters.regime_type}
                    onChange={e => handleFilterChange('regime_type', e.target.value)}
                    className="rpa-filter-select"
                >
                    <option value="">All Regimes</option>
                    {Object.keys(REGIME_LABELS).filter(k => k !== 'UNKNOWN').map(r => (
                        <option key={r} value={r}>{REGIME_LABELS[r]}</option>
                    ))}
                </select>

                <input
                    type="number"
                    className="rpa-filter-input"
                    placeholder="Min ML Conf"
                    step="0.05"
                    min="0"
                    max="1"
                    value={filters.min_confidence}
                    onChange={e => handleFilterChange('min_confidence', e.target.value)}
                />

                <label className="rpa-filter-toggle">
                    <input
                        type="checkbox"
                        checked={filters.regime_flip_only}
                        onChange={e => handleFilterChange('regime_flip_only', e.target.checked)}
                    />
                    <span>Regime Flips Only</span>
                </label>
            </div>

            {error && <div className="rpa-error">{error}</div>}

            {loading ? (
                <div className="rpa-loading">
                    <div className="rpa-spinner" />
                    <span>Analyzing signal attribution...</span>
                </div>
            ) : (
                <>
                    {/* ── Summary Strip ── */}
                    <div className="rpa-summary-strip">
                        <StatBadge label="Total Signals" value={header.total_signals || 0} />
                        <StatBadge label="Win Rate" value={`${header.win_rate || 0}%`} accent={header.win_rate > 50 ? 'positive' : 'negative'} />
                        <StatBadge label="Winners" value={header.winners_count || 0} accent="positive" />
                        <StatBadge label="Losers" value={header.losers_count || 0} accent="negative" />
                        <StatBadge label="Avg R (W)" value={header.avg_r_winners || 0} accent="positive" />
                        <StatBadge label="Avg R (L)" value={header.avg_r_losers || 0} accent="negative" />
                        <StatBadge label="Flip Rate" value={`${header.regime_flip_rate || 0}%`} />
                        <StatBadge label="Stability" value={header.stability_index || 0} />
                    </div>

                    {/* ── Regime Breakdown Heatmap ── */}
                    {Object.keys(regimeBreakdown).length > 0 && (
                        <div className="rpa-regime-heatmap">
                            <h4 className="rpa-section-title">Regime Performance Heatmap</h4>
                            <div className="rpa-heatmap-grid">
                                {Object.entries(regimeBreakdown).map(([regime, stats]) => (
                                    <div key={regime} className="rpa-heatmap-cell" style={{
                                        background: `linear-gradient(135deg, rgba(${stats.win_rate > 50 ? '16,185,129' : '239,68,68'}, ${Math.min(stats.win_rate / 100 * 0.3, 0.3)}) 0%, transparent 100%)`
                                    }}>
                                        <RegimeBadge regime={regime} />
                                        <div className="rpa-heatmap-stats">
                                            <span className={stats.win_rate > 50 ? 'win' : 'loss'}>{stats.win_rate}%</span>
                                            <span className="muted">({stats.wins}/{stats.total})</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Winners vs Losers Split Panel ── */}
                    <div className="rpa-split-panel">
                        {/* Winners */}
                        <div className="rpa-split-col">
                            <div className="rpa-split-header winners">
                                <span className="rpa-split-icon">🏆</span>
                                <span>Winners ({winners.length})</span>
                            </div>
                            <div className="rpa-signal-list">
                                {winners.length === 0 ? (
                                    <div className="rpa-empty">No winners in current filter</div>
                                ) : winners.map(sig => (
                                    <SignalRow key={sig.signal_id} signal={sig} type="winner" />
                                ))}
                            </div>
                        </div>

                        {/* Losers */}
                        <div className="rpa-split-col">
                            <div className="rpa-split-header losers">
                                <span className="rpa-split-icon">📉</span>
                                <span>Losers ({losers.length})</span>
                            </div>
                            <div className="rpa-signal-list">
                                {losers.length === 0 ? (
                                    <div className="rpa-empty">No losers in current filter</div>
                                ) : losers.map(sig => (
                                    <SignalRow key={sig.signal_id} signal={sig} type="loser" />
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* ── AI Forensic Analysis ── */}
                    <div className={`rpa-expandable ${expandedPanel === 'forensic' ? 'expanded' : ''}`}>
                        <button className="rpa-expand-btn" onClick={() => togglePanel('forensic')}>
                            <span className="rpa-expand-icon">🧠</span>
                            <span>AI Forensic Analysis</span>
                            <span className="rpa-chevron">{expandedPanel === 'forensic' ? '▾' : '▸'}</span>
                        </button>
                        {expandedPanel === 'forensic' && (
                            <div className="rpa-forensic-content">
                                <div className="rpa-forensic-section">
                                    <h5>Primary Attribution Drivers</h5>
                                    <ul className="rpa-driver-list">
                                        {(forensic.primary_drivers || []).map((d, i) => (
                                            <li key={i} className="rpa-driver-item">
                                                <span className="rpa-driver-bullet">▸</span>
                                                {d}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="rpa-forensic-section conclusion">
                                    <h5>Conclusion</h5>
                                    <pre className="rpa-conclusion-text">
                                        {forensic.conclusion || 'Insufficient data for analysis'}
                                    </pre>
                                </div>

                                {forensic.dimensions && (
                                    <div className="rpa-dimensions-grid">
                                        {Object.entries(forensic.dimensions).map(([key, dim]) => (
                                            <DimensionCard key={key} title={key} data={dim} />
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* ── Comparative Intelligence Matrix ── */}
                    <div className={`rpa-expandable ${expandedPanel === 'matrix' ? 'expanded' : ''}`}>
                        <button className="rpa-expand-btn" onClick={() => togglePanel('matrix')}>
                            <span className="rpa-expand-icon">📊</span>
                            <span>Comparative Intelligence Matrix</span>
                            <span className="rpa-chevron">{expandedPanel === 'matrix' ? '▾' : '▸'}</span>
                        </button>
                        {expandedPanel === 'matrix' && (
                            <div className="rpa-matrix-content">
                                <table className="rpa-matrix-table">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            <th>Winners Avg</th>
                                            <th>Losers Avg</th>
                                            <th>Delta</th>
                                            <th>Sig.</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {matrix.map((row, i) => (
                                            <tr key={i} className={row.significant ? 'significant' : ''}>
                                                <td className="metric-name">{row.metric}</td>
                                                <td className="win-val">{row.winners_avg}</td>
                                                <td className="loss-val">{row.losers_avg}</td>
                                                <td className={`delta-val ${row.delta > 0 ? 'positive' : row.delta < 0 ? 'negative' : ''}`}>
                                                    {row.delta > 0 ? '+' : ''}{row.delta}
                                                </td>
                                                <td>{row.significant ? <span className="sig-badge">●</span> : <span className="insig-badge">○</span>}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}


/* ── Sub-components ── */

function SignalRow({ signal, type }) {
    const isFlip = signal.regime_flip;
    return (
        <div className={`rpa-signal-row ${type} ${isFlip ? 'regime-flip' : ''}`}>
            <div className="rpa-sig-header">
                <span className="rpa-sig-symbol">{signal.symbol}</span>
                <span className={`rpa-sig-r ${signal.r_multiple >= 0 ? 'positive' : 'negative'}`}>
                    {signal.r_multiple >= 0 ? '+' : ''}{signal.r_multiple}R
                </span>
            </div>
            <div className="rpa-sig-details">
                <div className="rpa-sig-regimes">
                    <RegimeBadge regime={signal.regime_at_entry} />
                    <span className="rpa-arrow">→</span>
                    <RegimeBadge regime={signal.regime_at_exit} />
                    {isFlip && <span className="rpa-flip-flag">⚡ FLIP</span>}
                </div>
                <div className="rpa-sig-metrics">
                    <span title="ML Confidence">ML: {(signal.ml_confidence || 0).toFixed(2)}</span>
                    <span title="Score">S: {(signal.score || 0).toFixed(0)}</span>
                    <span title="Stability">St: {(signal.regime_stability || 0).toFixed(0)}</span>
                    <span title="Spread %tile">Sp: {(signal.spread_percentile || 0).toFixed(0)}</span>
                </div>
                {type === 'loser' && signal.failure_category && (
                    <div className="rpa-failure-tag">{signal.failure_category}</div>
                )}
            </div>
        </div>
    );
}

function DimensionCard({ title, data }) {
    const label = title.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    return (
        <div className="rpa-dimension-card">
            <h6>{label}</h6>
            <div className="rpa-dim-entries">
                {Object.entries(data).map(([k, v]) => (
                    <div key={k} className="rpa-dim-entry">
                        <span className="rpa-dim-key">{k.replace(/_/g, ' ')}</span>
                        <span className="rpa-dim-val">
                            {typeof v === 'boolean' ? (v ? '✓' : '✗') : typeof v === 'number' ? v.toFixed(2) : String(v)}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
