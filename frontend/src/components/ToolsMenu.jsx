import { useState, useEffect } from 'react'
import GlassCard from './GlassCard'
import { getMarketHours, convertCurrency } from '../services/api'
import './ToolsMenu.css'

export default function ToolsMenu() {
    const [activeTab, setActiveTab] = useState('hours')
    const [hours, setHours] = useState(null)
    const [converter, setConverter] = useState({ from: 'EUR', to: 'USD', amount: 1000, result: null })

    useEffect(() => {
        getMarketHours().then(r => setHours(r.data)).catch(() => setHours(MOCK_HOURS))
    }, [])

    const handleConvert = () => {
        convertCurrency({ from_currency: converter.from, to_currency: converter.to, amount: converter.amount })
            .then(r => setConverter(prev => ({ ...prev, result: r.data })))
            .catch(() => setConverter(prev => ({ ...prev, result: { rate: 1.0877, result: prev.amount * 1.0877 } })))
    }

    const hoursData = hours || MOCK_HOURS

    const tabs = [
        { key: 'hours', label: '🕐 Market Hours' },
        { key: 'converter', label: '💱 Converter' },
        { key: 'rates', label: '📈 Interest Rates' },
        { key: 'knowledge', label: '📚 Knowledge' },
    ]

    return (
        <GlassCard title="Trading Tools" icon="🛠" className="tools-card">
            <div className="tools-tabs">
                {tabs.map(t => (
                    <button key={t.key} className={`tool-tab ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>
                        {t.label}
                    </button>
                ))}
            </div>

            <div className="tools-content">
                {activeTab === 'hours' && (
                    <div className="market-hours">
                        {hoursData.sessions && Object.entries(hoursData.sessions).map(([name, info]) => (
                            <div key={name} className="session-row">
                                <span className={`session-dot ${info.open ? 'open' : 'closed'}`} />
                                <span className="session-name">{name}</span>
                                <span className="session-hours">{info.hours}</span>
                                <span className={`session-status ${info.open ? 'open' : 'closed'}`}>
                                    {info.open ? 'OPEN' : 'CLOSED'}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'converter' && (
                    <div className="converter">
                        <div className="converter-inputs">
                            <input type="number" value={converter.amount} onChange={e => setConverter(p => ({ ...p, amount: +e.target.value }))} />
                            <select value={converter.from} onChange={e => setConverter(p => ({ ...p, from: e.target.value }))}>
                                {['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'CHF', 'CAD'].map(c => <option key={c}>{c}</option>)}
                            </select>
                            <span className="converter-arrow">→</span>
                            <select value={converter.to} onChange={e => setConverter(p => ({ ...p, to: e.target.value }))}>
                                {['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CHF', 'CAD'].map(c => <option key={c}>{c}</option>)}
                            </select>
                            <button className="btn-primary btn-sm" onClick={handleConvert}>Convert</button>
                        </div>
                        {converter.result && (
                            <div className="converter-result">
                                <span className="result-amount">{converter.result.result?.toFixed(4)}</span>
                                <span className="result-rate">Rate: {converter.result.rate?.toFixed(5)}</span>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'rates' && (
                    <div className="rates-grid">
                        {RATES.map((r, i) => (
                            <div key={i} className="rate-row">
                                <span className="rate-bank">{r.bank}</span>
                                <span className="rate-value">{r.rate}</span>
                                <span className={`rate-bias ${r.bias}`}>{r.bias}</span>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'knowledge' && (
                    <div className="knowledge">
                        <div className="kb-item">📌 <strong>Pip Value</strong> — The value of a 1-pip move depends on lot size and currency pair.</div>
                        <div className="kb-item">📌 <strong>Risk Management</strong> — Never risk more than 1-2% of your account on a single trade.</div>
                        <div className="kb-item">📌 <strong>Major Sessions</strong> — London & New York overlap (12:00-16:00 UTC) sees highest volume.</div>
                        <div className="kb-item">📌 <strong>Carry Trade</strong> — Profit from interest rate differentials between currencies.</div>
                    </div>
                )}
            </div>
        </GlassCard>
    )
}

const MOCK_HOURS = {
    sessions: {
        sydney: { open: true, hours: '21:00 - 06:00 UTC' },
        tokyo: { open: true, hours: '00:00 - 09:00 UTC' },
        london: { open: false, hours: '07:00 - 16:00 UTC' },
        new_york: { open: false, hours: '12:00 - 21:00 UTC' },
    }
}

const RATES = [
    { bank: 'Federal Reserve (USD)', rate: '5.25-5.50%', bias: 'hawkish' },
    { bank: 'ECB (EUR)', rate: '4.50%', bias: 'neutral' },
    { bank: 'Bank of England (GBP)', rate: '5.25%', bias: 'hawkish' },
    { bank: 'Bank of Japan (JPY)', rate: '-0.10%', bias: 'dovish' },
    { bank: 'RBA (AUD)', rate: '4.35%', bias: 'neutral' },
    { bank: 'SNB (CHF)', rate: '1.75%', bias: 'neutral' },
]
