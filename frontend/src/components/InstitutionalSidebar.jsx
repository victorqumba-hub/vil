import React, { useState, useEffect, useMemo } from 'react';
import PerformanceSummaryWidget from './PerformanceSummaryWidget';
import SignalIntelligenceItem from './SignalIntelligenceItem';
import './InstitutionalSidebar.css';

const FILTERS = [
    { id: 'all', label: 'All Signals' },
    { id: 'ACTIVE', label: 'Active' },
    { id: 'PENDING', label: 'Pending' },
    { id: 'SUCCESS', label: 'Success' },
    { id: 'FAIL', label: 'Failed' },
];

const ASSET_CLASSES = [
    { id: 'all', label: 'All Assets' },
    { id: 'forex', label: 'Forex' },
    { id: 'index', label: 'Indices' },
    { id: 'commodity', label: 'Commodities' },
    { id: 'metal', label: 'Metals' },
    { id: 'crypto', label: 'Crypto' },
];

export default function InstitutionalSidebar({ initialSignals = [], onSignalSelect }) {
    const [signals, setSignals] = useState(initialSignals);
    const [statusFilter, setStatusFilter] = useState('all');
    const [assetFilter, setAssetFilter] = useState('all');
    const [selectedId, setSelectedId] = useState(null);
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Filter signals
    const filteredSignals = useMemo(() => {
        return signals.filter(s => {
            const statusMatch = statusFilter === 'all' || s.status?.startsWith(statusFilter);
            const assetMatch = assetFilter === 'all' || s.assetClass === assetFilter || s.asset_class === assetFilter;
            return statusMatch && assetMatch;
        });
    }, [signals, statusFilter, assetFilter]);

    // Handle incoming WebSocket signals
    // Note: Dashboard.jsx will pass new signals here if it manages the WS
    // or we can handle it here if passed a prop.
    useEffect(() => {
        if (initialSignals.length > 0) {
            setSignals(prev => {
                // Merge initial/new signals, avoiding duplicates by signalId
                const map = new Map(prev.map(s => [s.signalId || s.id, s]));
                initialSignals.forEach(s => {
                    const id = s.signalId || s.id;
                    if (map.has(id)) {
                        // Update existing signal (lifecycle change or score delta)
                        map.set(id, { ...map.get(id), ...s });
                    } else {
                        map.set(id, s);
                    }
                });
                return Array.from(map.values()).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            });
        }
    }, [initialSignals]);

    const handleSignalClick = (signal) => {
        setSelectedId(signal.signalId || signal.id);
        if (onSignalSelect) onSignalSelect(signal);
    };

    return (
        <aside className={`institutional-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <button
                className="collapse-toggle"
                onClick={() => setIsCollapsed(!isCollapsed)}
                style={{
                    position: 'absolute',
                    left: '-30px',
                    top: '20px',
                    background: '#12161c',
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: '#00e5ff',
                    padding: '5px',
                    cursor: 'pointer',
                    borderRadius: '4px 0 0 4px'
                }}
            >
                {isCollapsed ? '◀' : '▶'}
            </button>

            <div className="sidebar-header">
                <div className="sidebar-title">
                    <span style={{ color: '#00ff88' }}>●</span> Institutional Signal Monitoring System
                </div>
                <PerformanceSummaryWidget signals={signals} />
            </div>

            <div className="sidebar-filters">
                {ASSET_CLASSES.map(f => (
                    <div
                        key={f.id}
                        className={`filter-chip ${assetFilter === f.id ? 'active' : ''}`}
                        onClick={() => setAssetFilter(f.id)}
                    >
                        {f.label}
                    </div>
                ))}
            </div>

            <div className="sidebar-filters" style={{ borderBottom: 'none', background: 'transparent', paddingBottom: '0.5rem' }}>
                {FILTERS.map(f => (
                    <div
                        key={f.id}
                        className={`filter-chip ${statusFilter === f.id ? 'active' : ''}`}
                        onClick={() => setStatusFilter(f.id)}
                        style={{ fontSize: '0.65rem', padding: '0.2rem 0.6rem' }}
                    >
                        {f.label}
                    </div>
                ))}
            </div>

            <div className="signal-list">
                {filteredSignals.length > 0 ? (
                    filteredSignals.map(s => (
                        <SignalIntelligenceItem
                            key={s.signalId || s.id}
                            signal={s}
                            isSelected={selectedId === (s.signalId || s.id)}
                            onClick={handleSignalClick}
                        />
                    ))
                ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.5 }}>
                        No intelligence feeds for selected filters.
                    </div>
                )}
            </div>
        </aside>
    );
}
