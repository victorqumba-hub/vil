import GlassCard from './GlassCard'
import './PortfolioPanel.css'

export default function PortfolioPanel({ summary, trades = [] }) {
    const s = summary || {}

    return (
        <div className="portfolio-wrapper">
            <GlassCard title="Portfolio" icon="💼">
                <div className="portfolio-stats">
                    <div className="pf-stat">
                        <span className="pf-label">Total PnL</span>
                        <span className={`pf-value ${(s.total_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                            ${(s.total_pnl || 0).toFixed(2)}
                        </span>
                    </div>
                    <div className="pf-stat">
                        <span className="pf-label">Win Rate</span>
                        <span className="pf-value">{(s.win_rate || 0).toFixed(1)}%</span>
                    </div>
                    <div className="pf-stat">
                        <span className="pf-label">Trades</span>
                        <span className="pf-value">{s.total_trades || 0}</span>
                    </div>
                    <div className="pf-stat">
                        <span className="pf-label">Open</span>
                        <span className="pf-value accent">{s.open_trades || 0}</span>
                    </div>
                </div>

                <div className="pf-secondary">
                    <div className="pf-mini">
                        <span>Avg Win</span>
                        <span className="positive">${(s.avg_win || 0).toFixed(2)}</span>
                    </div>
                    <div className="pf-mini">
                        <span>Avg Loss</span>
                        <span className="negative">${(s.avg_loss || 0).toFixed(2)}</span>
                    </div>
                    <div className="pf-mini">
                        <span>W/L</span>
                        <span>{s.wins || 0} / {s.losses || 0}</span>
                    </div>
                </div>
            </GlassCard>

            {trades.length > 0 && (
                <GlassCard title="Recent Trades" icon="📋" className="trades-card">
                    <div className="trades-list">
                        {trades.slice(0, 8).map((t, i) => (
                            <div key={i} className="trade-row">
                                <span className="trade-sym">{t.symbol}</span>
                                <span className={`badge ${t.direction?.toLowerCase()}`}>{t.direction}</span>
                                <span className={`trade-status ${t.status?.toLowerCase()}`}>{t.status}</span>
                                <span className={`trade-pnl ${(t.pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                                    ${(t.pnl || 0).toFixed(2)}
                                </span>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            )}
        </div>
    )
}
