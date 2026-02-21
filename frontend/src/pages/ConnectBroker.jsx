import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { connectBroker } from '../services/api'
import './Auth.css'

export default function ConnectBroker() {
    const [form, setForm] = useState({
        account_id: '',
        api_key: '',
        environment: 'practice',
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [step, setStep] = useState('form') // 'form' | 'testing' | 'success'
    const [result, setResult] = useState(null)
    const nav = useNavigate()

    const updateField = (field) => (e) => {
        setForm(prev => ({ ...prev, [field]: e.target.value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setStep('testing')
        setLoading(true)

        try {
            const res = await connectBroker(form)
            setResult(res.data)
            setStep('success')
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to connect broker')
            setStep('form')
        } finally {
            setLoading(false)
        }
    }

    const goToDashboard = () => {
        nav('/dashboard')
    }

    return (
        <div className="auth-page">
            <div className="auth-bg">
                <div className="auth-orb orb-1" />
                <div className="auth-orb orb-2" />
                <div className="auth-orb orb-3" />
            </div>
            <div className="auth-card glass-card animate-in auth-card-wide">
                <div className="auth-header">
                    <Link to="/" className="auth-brand">
                        <span className="brand-icon">◆</span>
                        <span className="brand-text">VIL</span>
                    </Link>
                    <h2>Connect Your Broker</h2>
                    <p>Link your OANDA trading account to activate VIL</p>
                </div>

                {step === 'form' && (
                    <>
                        {error && <div className="auth-error">{error}</div>}

                        <div className="broker-info-banner">
                            <span className="info-icon">🔐</span>
                            <div>
                                <strong>Your credentials are encrypted</strong>
                                <p>API keys are stored using AES-256-GCM encryption. They are never stored in plaintext and are decrypted only at execution time.</p>
                            </div>
                        </div>

                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="form-group">
                                <label>OANDA Account ID *</label>
                                <div className="input-wrapper">
                                    <span className="input-icon">🏦</span>
                                    <input
                                        type="text"
                                        value={form.account_id}
                                        onChange={updateField('account_id')}
                                        placeholder="e.g. 101-004-XXXXXXX-001"
                                        required
                                        minLength={3}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>API Key (Personal Access Token) *</label>
                                <div className="input-wrapper">
                                    <span className="input-icon">🔑</span>
                                    <input
                                        type="password"
                                        value={form.api_key}
                                        onChange={updateField('api_key')}
                                        placeholder="Enter your OANDA API key"
                                        required
                                        minLength={10}
                                    />
                                </div>
                                <small className="form-hint">Found in OANDA Hub → Manage API Access</small>
                            </div>

                            <div className="form-group">
                                <label>Environment</label>
                                <div className="account-type-toggle">
                                    <button
                                        type="button"
                                        className={`type-btn ${form.environment === 'practice' ? 'active' : ''}`}
                                        onClick={() => setForm(prev => ({ ...prev, environment: 'practice' }))}
                                    >
                                        <span className="type-icon">🧪</span> Practice
                                    </button>
                                    <button
                                        type="button"
                                        className={`type-btn ${form.environment === 'live' ? 'active' : ''}`}
                                        onClick={() => setForm(prev => ({ ...prev, environment: 'live' }))}
                                    >
                                        <span className="type-icon">🔥</span> Live
                                    </button>
                                </div>
                            </div>

                            <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                                {loading ? 'Connecting...' : 'Connect & Verify'}
                            </button>
                        </form>

                        <div className="auth-footer">
                            <button className="btn-outline btn-sm" onClick={() => nav('/dashboard')} style={{ marginTop: '0.5rem' }}>
                                Skip for now
                            </button>
                        </div>
                    </>
                )}

                {step === 'testing' && (
                    <div className="broker-testing">
                        <div className="testing-animation">
                            <div className="pulse-ring" />
                            <div className="pulse-ring delay" />
                            <span className="testing-icon">🔄</span>
                        </div>
                        <h3>Validating Connection</h3>
                        <p>Testing your OANDA credentials and syncing account data...</p>
                    </div>
                )}

                {step === 'success' && result && (
                    <div className="broker-success">
                        <div className="success-icon-wrap">
                            <span className="success-icon">✅</span>
                        </div>
                        <h3>Broker Connected!</h3>
                        <p>Your OANDA account has been securely linked to VIL.</p>

                        <div className="broker-summary-card">
                            <div className="summary-row">
                                <span className="summary-label">Broker</span>
                                <span className="summary-value">OANDA</span>
                            </div>
                            <div className="summary-row">
                                <span className="summary-label">Account ID</span>
                                <span className="summary-value">{result.account_id}</span>
                            </div>
                            <div className="summary-row">
                                <span className="summary-label">Environment</span>
                                <span className="summary-value env-badge">{result.environment}</span>
                            </div>
                            <div className="summary-row">
                                <span className="summary-label">Balance</span>
                                <span className="summary-value">{result.cached_balance?.toLocaleString('en-US', { style: 'currency', currency: result.account_currency || 'USD' })}</span>
                            </div>
                            <div className="summary-row">
                                <span className="summary-label">API Key</span>
                                <span className="summary-value mono">{result.api_key_masked}</span>
                            </div>
                        </div>

                        <button className="btn-primary auth-submit" onClick={goToDashboard}>
                            Enter Dashboard →
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
