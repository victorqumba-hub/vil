import { useState, useEffect } from 'react'
import { getCalendar, getQuotes, getNews } from '../../services/api'
import '../GlassCard.css'

export default function MarketIntelligenceWidget() {
    const [activeTab, setActiveTab] = useState('calendar')
    const [calendar, setCalendar] = useState([])
    const [quotes, setQuotes] = useState([])

    useEffect(() => {
        getCalendar().then(r => setCalendar(r.data)).catch(() => { })
        getQuotes().then(r => setQuotes(r.data)).catch(() => { })
    }, [])

    const MOCK_CALENDAR = [
        { time: '13:30', currency: 'USD', event: 'Non-Farm Payrolls (Jan)', impact: 'high', forecast: '180K', actual: '353K' },
        { time: '13:30', currency: 'USD', event: 'Unemployment Rate', impact: 'high', forecast: '3.8%', actual: '3.7%' },
        { time: '14:45', currency: 'CAD', event: 'Ivey PMI (Jan)', impact: 'medium', forecast: '55.0', actual: '--' },
        { time: '15:00', currency: 'EUR', event: 'ECB President Lagarde Speech', impact: 'low', forecast: '--', actual: '--' },
        { time: '21:30', currency: 'AUD', event: 'Trade Balance', impact: 'medium', forecast: '11.0B', actual: '--' },
    ]

    const displayCalendar = calendar.length ? calendar : MOCK_CALENDAR

    return (
        <div className="glass-card full-height">
            <div className="card-header flex-header">
                <h3 className="card-title">Market Intelligence</h3>
                <div className="header-tabs">
                    <button className={`header-tab ${activeTab === 'calendar' ? 'active' : ''}`} onClick={() => setActiveTab('calendar')}>Economic Calendar</button>
                    <button className={`header-tab ${activeTab === 'quotes' ? 'active' : ''}`} onClick={() => setActiveTab('quotes')}>Market Quotes</button>
                    <button className={`header-tab ${activeTab === 'news' ? 'active' : ''}`} onClick={() => setActiveTab('news')}>Global News</button>
                </div>
                <div className="live-indicator">
                    <span>Data delayed by 5ms</span>
                    <span className="dot-green"></span>
                </div>
            </div>

            <div className="card-content no-padding table-container">
                {activeTab === 'calendar' && (
                    <table className="dark-table">
                        <thead>
                            <tr>
                                <th>Time (UTC)</th>
                                <th>Asset</th>
                                <th>Event</th>
                                <th>Impact</th>
                                <th>Forecast</th>
                                <th>Actual</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayCalendar.map((ev, i) => (
                                <tr key={i}>
                                    <td>{ev.time?.substring(11, 16) || ev.time}</td>
                                    <td><b className="text-white">{ev.currency}</b></td>
                                    <td>{ev.event}</td>
                                    <td><span className={`badge-impact ${ev.impact?.toLowerCase()}`}>{ev.impact?.toUpperCase() || 'LOW'}</span></td>
                                    <td>{ev.forecast || '--'}</td>
                                    <td className="text-green">{ev.actual || ev.previous || '--'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {activeTab === 'quotes' && (
                    <table className="dark-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Bid</th>
                                <th>Ask</th>
                                <th>Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            {quotes.length > 0 ? quotes.slice(0, 5).map((q, i) => (
                                <tr key={i}>
                                    <td><b className="text-white">{q.symbol}</b></td>
                                    <td>{q.bid}</td>
                                    <td>{q.ask}</td>
                                    <td className={q.change >= 0 ? 'text-green' : 'text-red'}>{q.change}%</td>
                                </tr>
                            )) : (
                                <tr><td colSpan="4" className="text-center">Loading Quotes...</td></tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
