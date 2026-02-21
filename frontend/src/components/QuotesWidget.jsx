import { useEffect, useState } from 'react'
import GlassCard from './GlassCard'
import { getQuotes } from '../services/api'
import './QuotesWidget.css'

export default function QuotesWidget() {
    const [quotes, setQuotes] = useState([])

    useEffect(() => {
        getQuotes()
            .then(r => setQuotes(r.data))
            .catch(() => setQuotes(MOCK_QUOTES))
    }, [])

    const data = quotes.length ? quotes : MOCK_QUOTES

    return (
        <GlassCard title="Live Quotes" icon="📊" className="quotes-card">
            <div className="quotes-grid">
                {data.map((q, i) => (
                    <div key={i} className="quote-row animate-in" style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="quote-symbol">
                            <span className={`quote-type-dot ${q.type}`} />
                            {q.symbol}
                        </div>
                        <div className="quote-price">{q.bid?.toFixed(q.bid > 100 ? 2 : 5)}</div>
                        <div className={`quote-change ${q.change >= 0 ? 'positive' : 'negative'}`}>
                            {q.change >= 0 ? '▲' : '▼'} {Math.abs(q.change).toFixed(2)}%
                        </div>
                    </div>
                ))}
            </div>
        </GlassCard>
    )
}

const MOCK_QUOTES = [
    { symbol: 'EUR/USD', bid: 1.0876, change: 0.12, type: 'forex' },
    { symbol: 'GBP/USD', bid: 1.2652, change: -0.08, type: 'forex' },
    { symbol: 'USD/JPY', bid: 150.42, change: 0.25, type: 'forex' },
    { symbol: 'AUD/USD', bid: 0.6543, change: -0.15, type: 'forex' },
    { symbol: 'XAU/USD', bid: 2045.50, change: 0.65, type: 'commodity' },
    { symbol: 'BTC/USD', bid: 95420.0, change: 1.23, type: 'crypto' },
    { symbol: 'ETH/USD', bid: 3245.0, change: 0.87, type: 'crypto' },
    { symbol: 'US500', bid: 5025.5, change: 0.35, type: 'index' },
]
