import '../GlassCard.css'

export default function LiveMarketStrip() {
    const MARKETS = [
        { sym: 'AAPL', name: 'APPLE INC.', price: '$185.85', change: '+1.24%', trend: 'up' },
        { sym: 'TSLA', name: 'TESLA, INC.', price: '$188.13', change: '-0.82%', trend: 'down' },
        { sym: 'NVDA', name: 'NVIDIA CORP.', price: '$661.60', change: '+4.97%', trend: 'up' },
        { sym: 'XAU/USD', name: 'GOLD / US DOLLAR', price: '2039.42', change: '+0.01%', trend: 'flat' },
    ]

    return (
        <div className="market-strip">
            <h2 className="section-title mb-4">Live Markets</h2>
            <div className="strip-grid">
                {MARKETS.map((m, i) => (
                    <div key={i} className={`market-mini-card ${m.trend}`}>
                        <div className="mini-card-header">
                            <div>
                                <div className="mini-sym">{m.sym}</div>
                                <div className="mini-name">{m.name}</div>
                            </div>
                            <div className="mini-icon">
                                {m.trend === 'up' ? '↗' : (m.trend === 'down' ? '↘' : '—')}
                            </div>
                        </div>
                        <div className="mini-price">{m.price}</div>
                        <div className={`mini-change ${m.trend === 'up' ? 'text-green' : 'text-red'}`}>
                            {m.change}
                        </div>
                        {/* Abstract chart decoration */}
                        <div className="mini-chart-deco">
                            <svg viewBox="0 0 100 20" className="chart-svg">
                                <path
                                    d={m.trend === 'up' ? "M0,20 Q25,15 50,10 T100,0" : "M0,0 Q25,5 50,15 T100,20"}
                                    fill="none"
                                    stroke={m.trend === 'up' ? "#10B981" : "#EF4444"}
                                    strokeWidth="2"
                                />
                            </svg>
                        </div>
                    </div>
                ))}
            </div>
            <div className="strip-actions text-right mt-2">
                <div className="btn-group">
                    <button className="btn-filter active">Currencies</button>
                    <button className="btn-filter">Cryptocurrencies</button>
                    <button className="btn-filter">Commodities</button>
                    <button className="btn-filter">Indices</button>
                </div>
            </div>
        </div>
    )
}
