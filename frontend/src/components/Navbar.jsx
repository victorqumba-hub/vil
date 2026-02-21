import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import './Navbar.css'

export default function Navbar() {
    const [open, setOpen] = useState(false)
    const location = useLocation()
    const isAuth = !!localStorage.getItem('vil_token')

    return (
        <nav className="navbar">
            <div className="container navbar-inner">
                <Link to="/" className="navbar-brand">
                    <span className="brand-icon">◆</span>
                    <span className="brand-text">VIL</span>
                    <span className="brand-tagline">Institutional Logic</span>
                </Link>

                <button className="nav-toggle" onClick={() => setOpen(!open)} aria-label="Menu">
                    <span className={`toggle-bar ${open ? 'open' : ''}`} />
                    <span className={`toggle-bar ${open ? 'open' : ''}`} />
                    <span className={`toggle-bar ${open ? 'open' : ''}`} />
                </button>

                <div className={`nav-links ${open ? 'show' : ''}`}>
                    <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Home</Link>
                    <a href="#calendar">Calendar</a>
                    <a href="#news">News</a>
                    <a href="#quotes">Quotes</a>
                    <a href="#tools">Tools</a>
                    <div className="nav-cta">
                        {isAuth ? (
                            <Link to="/dashboard" className="btn-primary btn-sm">Dashboard</Link>
                        ) : (
                            <>
                                <Link to="/login" className="btn-outline btn-sm">Sign In</Link>
                                <Link to="/register" className="btn-primary btn-sm">Get Started</Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    )
}
