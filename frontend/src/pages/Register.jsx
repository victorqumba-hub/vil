import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register as registerApi } from '../services/api'
import './Auth.css'

const COUNTRIES = [
    'South Africa', 'United States', 'United Kingdom', 'Nigeria', 'Kenya',
    'Australia', 'Canada', 'Germany', 'India', 'Japan', 'Singapore',
    'United Arab Emirates', 'Switzerland', 'Netherlands', 'France', 'Other'
]

function getPasswordStrength(pw) {
    let score = 0
    if (pw.length >= 12) score++
    if (/[A-Z]/.test(pw)) score++
    if (/[a-z]/.test(pw)) score++
    if (/\d/.test(pw)) score++
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pw)) score++
    return score
}

function getStrengthLabel(score) {
    if (score <= 1) return { label: 'Very Weak', color: '#ff4d4f', width: '20%' }
    if (score === 2) return { label: 'Weak', color: '#ff7a45', width: '40%' }
    if (score === 3) return { label: 'Fair', color: '#ffc53d', width: '60%' }
    if (score === 4) return { label: 'Strong', color: '#73d13d', width: '80%' }
    return { label: 'Excellent', color: '#36cfc9', width: '100%' }
}

export default function Register() {
    const [form, setForm] = useState({
        email: '', password: '', full_name: '', phone: '', country: '',
        account_type: 'demo', accept_terms: false,
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const nav = useNavigate()

    const strength = getPasswordStrength(form.password)
    const strengthInfo = getStrengthLabel(strength)

    const updateField = (field) => (e) => {
        const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
        setForm(prev => ({ ...prev, [field]: val }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        // Client-side validation
        if (form.password.length < 12) return setError('Password must be at least 12 characters')
        if (!/[A-Z]/.test(form.password)) return setError('Password needs an uppercase letter')
        if (!/[a-z]/.test(form.password)) return setError('Password needs a lowercase letter')
        if (!/\d/.test(form.password)) return setError('Password needs a digit')
        if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(form.password)) return setError('Password needs a special character')
        if (!form.accept_terms) return setError('You must accept the Terms & Risk Disclosure')

        setLoading(true)
        try {
            const res = await registerApi(form)
            localStorage.setItem('vil_token', res.data.access_token)
            if (res.data.refresh_token) {
                localStorage.setItem('vil_refresh_token', res.data.refresh_token)
            }
            nav('/connect-broker')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
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
                    <h2>Create Your Account</h2>
                    <p>Start your institutional trading journey</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-row">
                        <div className="form-group">
                            <label>Full Name *</label>
                            <div className="input-wrapper">
                                <span className="input-icon">👤</span>
                                <input type="text" value={form.full_name} onChange={updateField('full_name')} placeholder="Victor Doe" required minLength={2} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Email *</label>
                            <div className="input-wrapper">
                                <span className="input-icon">✉</span>
                                <input type="email" value={form.email} onChange={updateField('email')} placeholder="you@example.com" required />
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Password *</label>
                        <div className="input-wrapper">
                            <span className="input-icon">🔒</span>
                            <input type="password" value={form.password} onChange={updateField('password')} placeholder="Min 12 chars, upper, lower, digit, special" required minLength={12} />
                        </div>
                        {form.password && (
                            <div className="password-strength">
                                <div className="strength-bar">
                                    <div className="strength-fill" style={{ width: strengthInfo.width, background: strengthInfo.color }} />
                                </div>
                                <span className="strength-label" style={{ color: strengthInfo.color }}>{strengthInfo.label}</span>
                            </div>
                        )}
                        <div className="password-rules">
                            <span className={form.password.length >= 12 ? 'rule-pass' : 'rule-fail'}>12+ chars</span>
                            <span className={/[A-Z]/.test(form.password) ? 'rule-pass' : 'rule-fail'}>A-Z</span>
                            <span className={/[a-z]/.test(form.password) ? 'rule-pass' : 'rule-fail'}>a-z</span>
                            <span className={/\d/.test(form.password) ? 'rule-pass' : 'rule-fail'}>0-9</span>
                            <span className={/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(form.password) ? 'rule-pass' : 'rule-fail'}>!@#</span>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Phone <span className="optional">(optional)</span></label>
                            <div className="input-wrapper">
                                <span className="input-icon">📱</span>
                                <input type="tel" value={form.phone} onChange={updateField('phone')} placeholder="+27 123 456 7890" />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Country</label>
                            <select value={form.country} onChange={updateField('country')} className="auth-select">
                                <option value="">Select country</option>
                                {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Account Type</label>
                        <div className="account-type-toggle">
                            <button
                                type="button"
                                className={`type-btn ${form.account_type === 'demo' ? 'active' : ''}`}
                                onClick={() => setForm(prev => ({ ...prev, account_type: 'demo' }))}
                            >
                                <span className="type-icon">🧪</span> Demo
                            </button>
                            <button
                                type="button"
                                className={`type-btn ${form.account_type === 'live' ? 'active' : ''}`}
                                onClick={() => setForm(prev => ({ ...prev, account_type: 'live' }))}
                            >
                                <span className="type-icon">🔥</span> Live
                            </button>
                        </div>
                    </div>

                    <div className="form-group terms-group">
                        <label className="checkbox-container">
                            <input type="checkbox" checked={form.accept_terms} onChange={updateField('accept_terms')} />
                            <span className="checkmark"></span>
                            I accept the <a href="#" className="terms-link">Terms of Service</a> and <a href="#" className="terms-link">Risk Disclosure</a>
                        </label>
                    </div>

                    <button type="submit" className="btn-primary auth-submit" disabled={loading || !form.accept_terms}>
                        {loading ? (
                            <span className="spinner-loader">
                                <span className="spinner-dot"></span>
                                <span className="spinner-dot"></span>
                                <span className="spinner-dot"></span>
                            </span>
                        ) : 'Create Account'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <Link to="/login" className="footer-link">Sign in</Link></p>
                </div>
            </div>
        </div>
    )
}
