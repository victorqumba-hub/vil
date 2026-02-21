import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login as loginApi } from '../services/api'
import './Auth.css'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const nav = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const res = await loginApi({ email, password })
            localStorage.setItem('vil_token', res.data.access_token)
            if (res.data.refresh_token) {
                localStorage.setItem('vil_refresh_token', res.data.refresh_token)
            }
            nav('/dashboard')
        } catch (err) {
            const detail = err.response?.data?.detail || 'Login failed'
            const status = err.response?.status
            if (status === 423) {
                setError(`🔒 ${detail}`)
            } else if (status === 401) {
                setError('Invalid email or password')
            } else {
                setError(detail)
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-bg">
                <div className="auth-orb orb-1" />
                <div className="auth-orb orb-2" />
            </div>
            <div className="auth-card glass-card animate-in">
                <div className="auth-header">
                    <Link to="/" className="auth-brand">
                        <span className="brand-icon">◆</span>
                        <span className="brand-text">VIL</span>
                    </Link>
                    <h2>Welcome Back</h2>
                    <p>Sign in to access your trading dashboard</p>
                </div>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <div className="input-wrapper">
                            <span className="input-icon">✉</span>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                            />
                        </div>
                    </div>
                    <div className="form-group">
                        <div className="label-row">
                            <label htmlFor="password">Password</label>
                            <Link to="/forgot-password" title="Coming soon!" className="forgot-link">Forgot password?</Link>
                        </div>
                        <div className="input-wrapper">
                            <span className="input-icon">🔒</span>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                placeholder="••••••••••••"
                                required
                            />
                        </div>
                    </div>

                    <div className="form-options">
                        <label className="checkbox-container">
                            <input type="checkbox" />
                            <span className="checkmark"></span>
                            Remember me
                        </label>
                    </div>

                    <button type="submit" className="btn-primary auth-submit" disabled={loading}>
                        {loading ? (
                            <span className="spinner-loader">
                                <span className="spinner-dot"></span>
                                <span className="spinner-dot"></span>
                                <span className="spinner-dot"></span>
                            </span>
                        ) : 'Sign In'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Don't have an account? <Link to="/register" className="footer-link">Create one</Link></p>
                    <div className="auth-demo-card">
                        <span className="demo-badge">DEMO ACCESS</span>
                        <div className="demo-creds">
                            <code>demo@vil.io</code>
                            <code>DemoTrader@2026</code>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
