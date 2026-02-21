import { useState, useEffect } from 'react'
import GlassCard from './GlassCard'
import { getBrokerAccount, getBrokerTrades, getBrokerStats } from '../services/api'
import './OandaRiskTerminal.css'

export default function OandaRiskTerminal() {
    const [account, setAccount] = useState(null)
    const [trades, setTrades] = useState({ open: [], history: [] })
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [view, setView] = useState('open') // 'open' or 'history'

    const fetchData = async (isSilent = false) => {
        if (!isSilent) setLoading(true)
        else setRefreshing(true)

        try {
            const [accRes, tradeRes, statRes] = await Promise.all([
                getBrokerAccount(),
                getBrokerTrades(),
                getBrokerStats()
            ])
            setAccount(accRes.data)
            setTrades(tradeRes.data)
            setStats(statRes.data)
        } catch (err) {
            console.error('[OandaRiskTerminal] Fetch failed:', err)
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(() => fetchData(true), 5000) // Poll every 5s
        return () => clearInterval(interval)
    }, [])

    if (loading && !account) {
        return <div className="risk-terminal-loading">Syncing with OANDA...</div>
    }

    const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0)

    return (
        <div className="oanda-risk-terminal">
            {/* ── Section 1: Capital Monitor ─────────────────────────────── */}
            <GlassCard title="Live Demo Account" icon="🛡️" className="capital-monitor">
                <div className="terminal-header-badges">
                    <span className="badge demo">DEMO ACCOUNT</span>
                    <span className={`sync-indicator ${refreshing ? 'syncing' : 'synced'}`}>
                        {refreshing ? 'Updating...' : 'Live'}
                    </span>
                </div>

                <div className="capital-grid">
                    <div className="cap-item main">
                        <span className="cap-label">Equity (NAV)</span>
                        <span className="cap-value highlighted">{formatCurrency(account?.equity)}</span>
                    </div>
                    <div className="cap-item">
                        <span className="cap-label">Balance</span>
                        <span className="cap-value">{formatCurrency(account?.balance)}</span>
                    </div>
                    <div className="cap-item">
                        <span className="cap-label">Floating PnL</span>
                        <span className={`cap-value ${(account?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                            {formatCurrency(account?.unrealized_pnl)}
                        </span>
                    </div>
                </div>

                <div className="margin-strip">
                    <div className="margin-item">
                        <span className="m-label">Margin Used</span>
                        <span className="m-value">{formatCurrency(account?.margin_used)}</span>
                    </div>
                    <div className="margin-item">
                        <span className="m-label">Margin Available</span>
                        <span className="m-value">{formatCurrency(account?.margin_available)}</span>
                    </div>
                    <div className="margin-item">
                        <span className="m-label">Margin Level</span>
                        <span className={`m-value ${account?.margin_level > 200 ? 'safe' : 'risk'}`}>
                            {(account?.margin_level || 0).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </GlassCard>

            {/* ── Section 2: Execution Log ─────────────────────────────────── */}
            <GlassCard title="Execution Log" icon="⚡" className="execution-card">
                <div className="terminal-tabs">
                    <button className={view === 'open' ? 'active' : ''} onClick={() => setView('open')}>
                        Open Positions ({trades.open.length})
                    </button>
                    <button className={view === 'history' ? 'active' : ''} onClick={() => setView('history')}>
                        History
                    </button>
                </div>

                <div className="execution-table-wrapper">
                    <table className="execution-table">
                        <thead>
                            <tr>
                                <th>Instrument</th>
                                <th>Side</th>
                                <th>Size</th>
                                <th>Entry</th>
                                <th>PnL</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(view === 'open' ? trades.open : trades.history).map((t, i) => (
                                <tr key={i} className="execution-row">
                                    <td className="sym-cell">
                                        <span className="sym">{t.symbol}</span>
                                        <span className="broker-id">ID: {t.broker_order_id}</span>
                                    </td>
                                    <td><span className={`side-badge ${t.direction.toLowerCase()}`}>{t.direction}</span></td>
                                    <td>{Math.abs(t.units)}</td>
                                    <td>{t.entry_price.toFixed(5)}</td>
                                    <td className={(t.unrealized_pnl || t.realized_pnl) >= 0 ? 'positive' : 'negative'}>
                                        {formatCurrency(t.unrealized_pnl || t.realized_pnl)}
                                    </td>
                                    <td>
                                        <span className={`status-badge ${t.status.toLowerCase()}`}>
                                            {t.status === 'OPEN' ? 'AUTO' : t.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {(view === 'open' ? trades.open : trades.history).length === 0 && (
                                <tr><td colSpan="6" className="empty-cell">No {view} trades found.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </GlassCard>

            {/* ── Section 3: Performance Quick View ───────────────────────── */}
            <div className="stats-row">
                <div className="stat-box">
                    <span className="stat-label">Automation Win Rate</span>
                    <span className="stat-value">{stats?.win_rate || 0}%</span>
                </div>
                <div className="stat-box">
                    <span className="stat-label">Total Realized PnL</span>
                    <span className={`stat-value ${(stats?.total_realized || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {formatCurrency(stats?.total_realized)}
                    </span>
                </div>
            </div>
        </div>
    )
}
