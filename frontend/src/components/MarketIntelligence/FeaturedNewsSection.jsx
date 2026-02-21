import '../GlassCard.css'

export default function FeaturedNewsSection() {
    return (
        <div className="news-analysis-grid">
            <div className="glass-card news-mid-card">
                <div className="card-header flex-between">
                    <span className="card-title-sm icon-title">📰 Global News Feed</span>
                    <button className="btn-text">View All</button>
                </div>
                <div className="news-item-row">
                    <div className="news-meta">
                        <span>REUTERS • 12M AGO</span>
                        <span className="badge-bullish">82% BULLISH</span>
                    </div>
                    <div className="news-headline">
                        US Treasury yields dip as investors weigh latest job market data and Fed commentary.
                    </div>
                </div>
                <div className="news-item-row">
                    <div className="news-meta">
                        <span>BLOOMBERG • 34M AGO</span>
                        <span className="badge-neutral">NEUTRAL</span>
                    </div>
                    <div className="news-headline">
                        European Central Bank maintains status quo, highlighting lingering inflation risks.
                    </div>
                </div>
                <div className="news-item-row">
                    <div className="news-meta">
                        <span>WSJ • 1H AGO</span>
                        <span className="badge-bearish">64% BEARISH</span>
                    </div>
                    <div className="news-headline">
                        Crude oil prices under pressure as global demand concerns resurface amid geopolitical shifts.
                    </div>
                </div>
            </div>

            <div className="glass-card analysis-card">
                <div className="card-header">
                    <span className="badge-blue">FEATURED ANALYSIS</span>
                </div>
                <div className="analysis-content">
                    <h3 className="analysis-title">The AI Alpha: How Machine Learning is Transforming Liquidity Pools</h3>
                    <p className="analysis-desc">
                        Dive deep into our latest whitepaper on predictive liquidity management in highly volatile equity markets.
                    </p>
                    <button className="btn-primary mt-3">Read Full Paper →</button>
                </div>
            </div>
        </div>
    )
}
