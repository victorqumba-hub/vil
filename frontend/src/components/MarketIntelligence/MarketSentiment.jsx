import '../GlassCard.css'

export default function MarketSentiment() {
    return (
        <div className="glass-card mt-4">
            <div className="card-header">
                <h3 className="card-title">Market Sentiment Index</h3>
            </div>
            <div className="card-content">
                <div className="sentiment-row mb-3">
                    <div className="flex-between mb-1">
                        <span className="sent-label">S&P 500</span>
                        <span className="sent-val text-green">74% EXTREME GREED</span>
                    </div>
                    <div className="progress-bar-bg">
                        <div className="progress-bar-fill bg-green" style={{ width: '74%' }}></div>
                    </div>
                </div>

                <div className="sentiment-row mb-3">
                    <div className="flex-between mb-1">
                        <span className="sent-label">CRYPTO INDEX</span>
                        <span className="sent-val text-green">62% GREED</span>
                    </div>
                    <div className="progress-bar-bg">
                        <div className="progress-bar-fill bg-green" style={{ width: '62%' }}></div>
                    </div>
                </div>

                <div className="sentiment-row">
                    <div className="flex-between mb-1">
                        <span className="sent-label">US DOLLAR</span>
                        <span className="sent-val text-red">28% FEAR</span>
                    </div>
                    <div className="progress-bar-bg">
                        <div className="progress-bar-fill bg-red" style={{ width: '28%' }}></div>
                    </div>
                </div>
            </div>
        </div>
    )
}
