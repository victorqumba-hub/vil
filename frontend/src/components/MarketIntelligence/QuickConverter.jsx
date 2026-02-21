import { useState } from 'react'
import '../GlassCard.css'

export default function QuickConverter() {
    const [amount, setAmount] = useState(1.00)
    const [from, setFrom] = useState('BTC')
    const [to, setTo] = useState('USD')
    const [result, setResult] = useState(43281.50)

    const handleConvert = () => {
        // Mock conversion logic for UI demo
        if (from === 'BTC' && to === 'USD') setResult(amount * 43281.50)
        else if (from === 'ETH' && to === 'USD') setResult(amount * 2281.50)
        else setResult(amount * 1.0)
    }

    return (
        <div className="glass-card full-height">
            <div className="card-header">
                <h3 className="card-title">QUICK CONVERTER</h3>
            </div>
            <div className="card-content">
                <div className="converter-form">
                    <div className="input-group">
                        <label>SELL</label>
                        <div className="input-wrapper">
                            <input
                                type="number"
                                value={amount}
                                onChange={e => setAmount(parseFloat(e.target.value))}
                                className="dark-input"
                            />
                            <span className="currency-tag">{from}</span>
                        </div>
                    </div>

                    <div className="converter-swap">
                        <button className="swap-btn" onClick={handleConvert}>⚡</button>
                    </div>

                    <div className="input-group">
                        <label>BUY</label>
                        <div className="input-wrapper">
                            <input
                                type="text"
                                readOnly
                                value={result.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                className="dark-input highlight-text"
                            />
                            <span className="currency-tag">{to}</span>
                        </div>
                    </div>

                    <button className="btn-primary full-width mt-4" style={{ height: '48px', fontSize: '1rem' }}>
                        Execute Institutional Trade
                    </button>
                    <p className="micro-text text-center mt-2 opacity-50">SPREADS STARTING FROM 0.001 PIPS</p>
                </div>
            </div>
        </div>
    )
}
