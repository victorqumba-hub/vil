import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import SignalCard from '../components/SignalCard'
import SignalChart from '../components/SignalChart'
import AIReportPanel from '../components/AIReportPanel'
import OandaRiskTerminal from '../components/OandaRiskTerminal'
import GlassCard from '../components/GlassCard'
import OandaScanner from '../components/OandaScanner'
import LiveSignalStream from '../components/LiveSignalStream'
import AssetIntelligencePanel from '../components/AssetIntelligencePanel'
import RiskMonitorPanel from '../components/RiskMonitorPanel'
import AuditPanel from '../components/AuditPanel'
import AdvancedAnalyticsPanel from '../components/AdvancedAnalyticsPanel'
import HistoricalLabPanel from '../components/HistoricalLabPanel'
import SignalIntelligenceLab from '../components/SignalIntelligenceLab'

import ToolsMenu from '../components/ToolsMenu'
import NewsWidget from '../components/NewsWidget'
import ForexCalendar from '../components/ForexCalendar'
import QuotesWidget from '../components/QuotesWidget'
import {
    getLiveSignals,
    getPortfolioSummary,
    getPortfolioTrades,
    getAIReports,
    getPipelineStatus,
    getBrokerAccount,
    getBrokerStatus,
    getMe,
} from '../services/api'
import { connectWebSocket } from '../services/ws'
import MobileAccountCard from '../components/MobileAccountCard'
import './Dashboard.css'
import './DashboardMobile.css'
import '../pages/Auth.css'

const ASSET_TABS = [
    { key: 'all', label: 'All', icon: '🌐' },
    { key: 'forex', label: 'Forex', icon: '💱' },
    { key: 'index', label: 'Indices', icon: '📈' },
    { key: 'commodity', label: 'Commodities', icon: '🛢️' },
    { key: 'metal', label: 'Metals', icon: '🥇' },
    { key: 'crypto', label: 'Crypto', icon: '₿' },
]

export default function Dashboard() {
    const nav = useNavigate()
    const [signals, setSignals] = useState([])
    const [portfolio, setPortfolio] = useState(null)
    const [trades, setTrades] = useState([])
    const [reports, setReports] = useState([])
    const [wsStatus, setWsStatus] = useState('connecting')
    const [wsSignals, setWsSignals] = useState([])
    const [selectedSignal, setSelectedSignal] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [pipelineStatus, setPipelineStatus] = useState(null)
    const [lastScanEvent, setLastScanEvent] = useState(null)
    const [brokerAccount, setBrokerAccount] = useState(null)
    const [activeTab, setActiveTab] = useState('all')
    const [activePanel, setActivePanel] = useState('pipeline')
    const [brokerConnected, setBrokerConnected] = useState(null) // null = loading, true/false
    const [currentUser, setCurrentUser] = useState(null)
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024)

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 1024)
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    const PANELS = [
        { id: 'pipeline', label: 'Signal Pipeline', icon: '📡' },
        { id: 'intelligence', label: 'Asset Intelligence', icon: '🧠' },
        { id: 'risk', label: 'Portfolio Risk', icon: '🛡️' },
        { id: 'audit', label: 'Score Audit', icon: '⚖️' },
        { id: 'analytics', label: 'Advanced Analytics', icon: '📊' },
        { id: 'history', label: 'Historical Lab', icon: '🔬' },
        { id: 'forensics', label: 'Intelligence Lab', icon: '🧪' },
    ]

    useEffect(() => {
        const token = localStorage.getItem('vil_token')
        if (!token) {
            nav('/login')
            return
        }

        // Fetch initial data
        const fetchData = async () => {
            try {
                setLoading(true)

                // Check user info and broker status
                try {
                    const [meRes, brokerStatusRes] = await Promise.all([
                        getMe(),
                        getBrokerStatus(),
                    ])
                    setCurrentUser(meRes.data)
                    setBrokerConnected(brokerStatusRes.data.connected)
                } catch (authErr) {
                    console.warn('[Dashboard] Auth/broker check failed:', authErr)
                    setBrokerConnected(false)
                }

                const assetClass = activeTab === 'all' ? undefined : activeTab
                const [sigRes, portRes, tradeRes, reportRes, statusRes, brokerRes] = await Promise.allSettled([
                    getLiveSignals(50, assetClass),
                    getPortfolioSummary(),
                    getPortfolioTrades(),
                    getAIReports(10),
                    getPipelineStatus(),
                    getBrokerAccount()
                ])

                // Defensive state updates
                if (sigRes.status === 'fulfilled') {
                    const sigData = Array.isArray(sigRes.value.data)
                        ? sigRes.value.data.filter(s => s && typeof s === 'object')
                        : [];
                    setSignals(sigData);
                    setWsSignals(sigData);
                }

                if (portRes.status === 'fulfilled') {
                    setPortfolio(portRes.value.data || null);
                }

                if (tradeRes.status === 'fulfilled') {
                    setTrades(Array.isArray(tradeRes.value.data) ? tradeRes.value.data : []);
                }

                if (reportRes.status === 'fulfilled') {
                    setReports(Array.isArray(reportRes.value.data) ? reportRes.value.data : []);
                }

                if (statusRes.status === 'fulfilled') {
                    setPipelineStatus(statusRes.value.data || null);
                }

                if (brokerRes.status === 'fulfilled') {
                    setBrokerAccount(brokerRes.value.data || null);
                }

                // If critical data failed (e.g. signals/portfolio), set a warning but don't crash
                if (sigRes.status === 'rejected' && portRes.status === 'rejected') {
                    setError("Limited connectivity: Unable to fetch core market data.");
                } else {
                    setError(null);
                }

            } catch (err) {
                console.error('[Dashboard] Critical failure:', err)
                if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                    localStorage.removeItem('vil_token')
                    nav('/login')
                    return
                }
                setError("Could not connect to the backend server.")
            } finally {
                setLoading(false)
            }
        }

        fetchData()

        // WebSocket for live signal updates
        const cleanup = connectWebSocket('signals', (msg) => {
            if (msg.type === 'pipeline_status') {
                setPipelineStatus(msg.data)
            } else if (msg.eventType === 'SIGNAL_UPDATE' || msg.eventType === 'SIGNAL_CREATED') {
                setWsSignals(prev => {
                    // Normalize to unified format
                    const normalized = {
                        ...msg,
                        id: msg.signalId || msg.id,
                        timestamp: msg.timestamp || new Date().toISOString()
                    };

                    // If it's just a creation stub without score/direction, we might want to ignore it 
                    // IF we expect a full update later, OR we can keep it if it has enough info.
                    // For now, let's ensure we only add if it has a symbol.
                    if (!normalized.symbol) return prev;

                    const exists = prev.find(s => (s.signalId || s.id) === normalized.id);
                    if (exists) {
                        return prev.map(s => (s.signalId || s.id) === normalized.id ? { ...s, ...normalized } : s);
                    }
                    return [normalized, ...prev].slice(0, 50);
                });
            } else if (msg.eventType === 'SCAN_EVENT') {
                setLastScanEvent(msg)
            } else if (msg.id || msg.signalId) {
                // Support legacy or direct signal message format
                setWsSignals(prev => {
                    const id = msg.id || msg.signalId;
                    const exists = prev.find(s => (s.id || s.signalId) === id);
                    if (exists) return prev;
                    return [msg, ...prev].slice(0, 50);
                });
            }
        })

        return cleanup
    }, [nav, activeTab])

    const handleLogout = () => {
        localStorage.removeItem('vil_token')
        localStorage.removeItem('vil_refresh_token')
        nav('/')
    }

    // Filter signals by active tab (client-side backup if API doesn't filter)
    const filteredSignals = activeTab === 'all'
        ? signals
        : signals.filter(s => s && s.asset_class === activeTab)

    if (loading && !portfolio && !error) {
        return (
            <div className="dashboard-loading">
                <div className="loader-content">
                    <div className="loader-spinner"></div>
                    <p>Securing Institutional Feed...</p>
                </div>
            </div>
        );
    }

    return (
        <div className={`dashboard ${isMobile ? 'mobile-view' : 'desktop-view'}`}>
            {/* REMOVED: Redundant Navbar — handled by AppShell */}

            {error && (
                <div className="container" style={{ paddingTop: '1rem' }}>
                    <div className="error-banner">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                            <span>{error}</span>
                        </div>
                        <button className="btn-outline btn-sm" onClick={() => window.location.reload()}>Retry Connection</button>
                    </div>
                </div>
            )}

            <div className="dash-header container">
                {!isMobile && (
                    <div className="dash-title-row">
                        <div>
                            <h1 className="dash-title">Institutional Terminal</h1>
                            <p className="dash-subtitle">
                                {currentUser && <span>Welcome, <strong>{currentUser.display_name || currentUser.full_name}</strong> · </span>}
                                Precision Intelligence & Signal Monitoring
                            </p>
                        </div>
                        <div className="dash-actions">
                            {brokerConnected !== null && (
                                <span className={`broker-status-badge ${brokerConnected ? 'connected' : 'disconnected'}`}>
                                    {brokerConnected ? '● Broker Live' : '○ No Broker'}
                                </span>
                            )}
                            <span className={`ws-indicator ${wsStatus}`}>
                                <span className="ws-dot" /> {wsStatus === 'connected' ? 'Live' : 'Connecting'}
                            </span>
                            <button className="btn-outline btn-sm" onClick={handleLogout}>Sign Out</button>
                        </div>
                    </div>
                )}

                {!isMobile && (
                    <div className="panel-tabs-scroll">
                        <div className="panel-tabs">
                            {PANELS.map(panel => (
                                <button
                                    key={panel.id}
                                    className={`panel-tab ${activePanel === panel.id ? 'active' : ''}`}
                                    onClick={() => setActivePanel(panel.id)}
                                >
                                    <span className="p-icon">{panel.icon}</span>
                                    <span className="p-label">{panel.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="dash-grid container">
                {isMobile ? (
                    /* 📱 MOBILE MOBILE-FIRST STACK */
                    <div className="mobile-dashboard-stack">
                        {/* SECTION 1 — Account Overview Card */}
                        <section className="dashboard-section" onClick={() => nav('/portfolio')}>
                            <MobileAccountCard data={portfolio} />
                        </section>

                        {/* SECTION 2 — Live Signal Stream (Condensed) */}
                        <section className="dashboard-section" onClick={() => nav('/signals')}>
                            <div className="section-header-mobile">
                                <h3 className="section-title">Live Signal Stream</h3>
                                <div className="asset-tabs-mini">
                                    {ASSET_TABS.slice(0, 4).map(tab => (
                                        <button
                                            key={tab.key}
                                            className={`mini-tab ${activeTab === tab.key ? 'active' : ''}`}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setActiveTab(tab.key);
                                            }}
                                        >
                                            {tab.icon}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <LiveSignalStream
                                signals={activeTab === 'all' ? wsSignals : wsSignals.filter(s => s.asset_class === activeTab || s.assetClass === activeTab)}
                                scanEvent={lastScanEvent}
                                onSignalSelect={setSelectedSignal}
                                variant="mobile-condensed"
                            />
                        </section>

                        {/* SECTION 3 — Portfolio Risk Panel */}
                        <section className="dashboard-section" onClick={() => nav('/portfolio')}>
                            <h3 className="section-title">Active Portfolio</h3>
                            <RiskMonitorPanel portfolio={portfolio} brokerAccount={brokerAccount} variant="mobile-cards" />
                        </section>

                        {/* SECTION 4 — Regime Intelligence Snapshot */}
                        <section className="dashboard-section">
                            <h3 className="section-title">Regime Intelligence</h3>
                            <div className="regime-snap-card glass-card">
                                <div className="snap-row">
                                    <span className="snap-label">Market Regime</span>
                                    <span className="snap-value highlight">TRENDING BULLISH</span>
                                </div>
                                <div className="snap-row">
                                    <span className="snap-label">Volatility State</span>
                                    <span className="snap-value">Normal (14.2%)</span>
                                </div>
                                <div className="snap-row">
                                    <span className="snap-label">Regime Duration</span>
                                    <span className="snap-value">4h 12m</span>
                                </div>
                            </div>
                        </section>

                        {/* SECTION 5 — Score Audit Summary */}
                        <section className="dashboard-section" onClick={() => nav('/audit')}>
                            <div className="section-header-mobile">
                                <h3 className="section-title">Performance Snapshot</h3>
                                <span className="view-link">View Audit ➔</span>
                            </div>
                            <div className="audit-snap-grid">
                                <div className="mini-stat-box glass-card">
                                    <span className="m-label">Win Rate</span>
                                    <span className="m-val">68%</span>
                                </div>
                                <div className="mini-stat-box glass-card">
                                    <span className="m-label">Avg R</span>
                                    <span className="m-val">2.4</span>
                                </div>
                            </div>
                        </section>
                    </div>
                ) : (
                    /* 💻 DESKTOP DYNAMIC PANELS */
                    <div className="desktop-panels-reveal">
                        {activePanel === 'pipeline' && (
                            <div className="grid-12 animate-in">
                                {/* ── ROW 1 (4-4-4) ─────────────────────────────────── */}
                                <section className="col-4">
                                    <h3 className="section-title">Account Overview</h3>
                                    <div className="glass-card">
                                        <MobileAccountCard data={portfolio} />
                                    </div>
                                </section>

                                <section className="col-4">
                                    <h3 className="section-title">Regime Intelligence</h3>
                                    <div className="glass-card">
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: 'var(--sp-xs)' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>PRIMARY REGIME</span>
                                                <span className="highlight" style={{ fontWeight: 800, color: 'var(--accent-blue)' }}>TRENDING BULLISH</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: 'var(--sp-xs)' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>VOLATILITY</span>
                                                <span style={{ fontWeight: 600 }}>STANDARD (15.4)</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>BIAS</span>
                                                <span className="text-green" style={{ fontWeight: 600 }}>OVERWEIGHT (+)</span>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                <section className="col-4">
                                    <h3 className="section-title">Risk Exposure</h3>
                                    <div className="glass-card">
                                        <RiskMonitorPanel portfolio={portfolio} variant="mobile-cards" />
                                    </div>
                                </section>

                                {/* ── ROW 2 (8-4) ───────────────────────────────────── */}
                                <section className="col-8">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <h3 className="section-title">Live Signal Stream</h3>
                                        <div className="asset-tabs" style={{ marginBottom: '8px', border: 'none', background: 'transparent' }}>
                                            {ASSET_TABS.map(tab => (
                                                <button
                                                    key={tab.key}
                                                    className={`asset-tab ${activeTab === tab.key ? 'active' : ''}`}
                                                    onClick={() => setActiveTab(tab.key)}
                                                    style={{ padding: '4px 12px', fontSize: '0.7rem' }}
                                                >
                                                    {tab.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                                        <LiveSignalStream
                                            signals={activeTab === 'all' ? wsSignals : wsSignals.filter(s => s.asset_class === activeTab || s.assetClass === activeTab)}
                                            scanEvent={lastScanEvent}
                                            onSignalSelect={setSelectedSignal}
                                            variant="desktop"
                                        />
                                    </div>
                                </section>

                                <section className="col-4">
                                    <h3 className="section-title">Portfolio Snapshot</h3>
                                    <div className="glass-card">
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-lg)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>DAILY CHANGE</span>
                                                <span className="text-green" style={{ fontWeight: 800, fontSize: '1.1rem' }}>+$2,840.12</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>OPEN TRADES</span>
                                                <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>{portfolio?.active_trades_count || 0}</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span className="text-muted" style={{ fontSize: '0.75rem' }}>MARGIN USAGE</span>
                                                <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>3.2%</span>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* ── ROW 3 (6-6) ───────────────────────────────────── */}
                                <section className="col-6">
                                    <h3 className="section-title">Institutional Score Audit</h3>
                                    <div className="glass-card">
                                        <AuditPanel />
                                    </div>
                                </section>

                                <section className="col-6">
                                    <h3 className="section-title">Liquidity Structure Map</h3>
                                    <div className="glass-card">
                                        <div style={{ textAlign: 'center', padding: 'var(--sp-xl)' }}>
                                            <div style={{ fontSize: '2.5rem', opacity: 0.3, marginBottom: 'var(--sp-md)' }}>📉</div>
                                            <p className="text-muted" style={{ fontSize: '0.85rem' }}>Connecting to institutional data feeds...</p>
                                        </div>
                                    </div>
                                </section>
                            </div>
                        )}

                        {activePanel === 'intelligence' && (
                            <div className="animate-in">
                                <AssetIntelligencePanel signals={wsSignals} />
                            </div>
                        )}

                        {activePanel === 'risk' && (
                            <div className="animate-in">
                                <div className="glass-card" style={{ padding: 'var(--sp-lg)' }}>
                                    <RiskMonitorPanel portfolio={portfolio} brokerAccount={brokerAccount} variant="desktop" />
                                </div>
                            </div>
                        )}

                        {activePanel === 'audit' && (
                            <div className="animate-in">
                                <div className="glass-card" style={{ padding: 'var(--sp-lg)' }}>
                                    <AuditPanel />
                                </div>
                            </div>
                        )}

                        {activePanel === 'analytics' && (
                            <div className="animate-in">
                                <div className="glass-card" style={{ padding: 'var(--sp-lg)' }}>
                                    <AdvancedAnalyticsPanel />
                                </div>
                            </div>
                        )}

                        {activePanel === 'history' && (
                            <div className="animate-in">
                                <div className="glass-card" style={{ padding: 'var(--sp-lg)' }}>
                                    <HistoricalLabPanel />
                                </div>
                            </div>
                        )}

                        {activePanel === 'forensics' && (
                            <div className="animate-in">
                                <section className="grid-12">
                                    <div className="col-12 glass-card">
                                        <SignalIntelligenceLab />
                                    </div>
                                </section>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
