import React, { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { Link } from 'react-router-dom'
import MarketIntelligenceSection from '../components/MarketIntelligence/MarketIntelligenceSection'
import './Landing.css'

export default function Landing() {
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 1024);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className={`landing ${isMobile ? 'pwa-landing' : ''}`}>
            <Navbar />

            {/* ── Hero Section ─────────────────────────────────────────── */}
            <section className="hero">
                <div className="hero-bg">
                    <div className="hero-orb orb-1" />
                    <div className="hero-orb orb-2" />
                    <div className="hero-grid-overlay" />
                </div>
                <div className="container hero-content">
                    <div className="hero-badge animate-in">AI-POWERED TRADING INTELLIGENCE</div>
                    <h1 className="hero-title animate-in-delay-1">
                        <span className="hero-gradient">Institutional-Grade</span>
                        <br />Signal Engine
                    </h1>
                    <p className="hero-subtitle animate-in-delay-2">
                        Multi-layered market analysis with six regime gate filters, AI-driven reports,
                        and real-time signal delivery. Trade with confidence.
                    </p>
                    <div className="hero-actions animate-in-delay-3">
                        <Link to="/register" className="btn-primary btn-lg">
                            Start Trading  →
                        </Link>
                        <Link to="/login" className="btn-outline btn-lg">
                            View Live Signals
                        </Link>
                    </div>
                </div>
            </section>

            {/* ── Market Intelligence Section (Overlapping) ────────────── */}
            <div className="market-intel-wrapper">
                <MarketIntelligenceSection />

                {/* ── System Stats Strip ───────────────────────────────── */}
                <div className="container mt-5">
                    <div className="stats-strip animate-in-delay-3">
                        <div className="stat-item">
                            <span className="stat-dot green"></span>
                            <span className="stat-label">SYSTEM ONLINE</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <span className="stat-val">6</span>
                            <span className="stat-label">GATE LAYERS</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <span className="stat-val">60+</span>
                            <span className="stat-label">ASSETS MONITORED</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <span className="stat-val">24/7</span>
                            <span className="stat-label">INSTITUTIONAL FEED</span>
                        </div>
                    </div>
                </div>
            </div>



            {/* ── Features Section ─────────────────────────────────────── */}
            <section className="features-section container">
                <div className="section-header">
                    <h2 className="section-title">Why VIL?</h2>
                    <p className="section-desc">Our proprietary six-layer regime gate system filters noise so you trade with clarity.</p>
                </div>
                <div className="features-grid">
                    {FEATURES.map((f, i) => (
                        <div key={i} className="feature-card glass-card animate-in" style={{ animationDelay: `${i * 0.1}s` }}>
                            <div className="feature-icon">{f.icon}</div>
                            <h3 className="feature-title">{f.title}</h3>
                            <p className="feature-desc">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── CTA Section ──────────────────────────────────────────── */}
            <section className="cta-section">
                <div className="container cta-content">
                    <h2 className="cta-title">Ready to Trade at Institutional Level?</h2>
                    <p className="cta-desc">Join traders who trust algorithmic analysis over guesswork.</p>
                    <Link to="/register" className="btn-primary btn-lg">Create Free Account  →</Link>
                </div>
            </section>

            <Footer />
        </div>
    )
}

const FEATURES = [
    { icon: '🎯', title: 'Precision Signals', desc: 'Multi-timeframe confluence with exact entry, SL, and TP levels scored by our proprietary engine.' },
    { icon: '🔬', title: 'Regime Classification', desc: 'Automatically classifies market conditions — trending, ranging, high volatility, or low activity.' },
    { icon: '🛡️', title: '6-Layer Gate System', desc: 'Volatility, trend, structural, breakout, event, and composite gates ensure only high-quality signals pass.' },
    { icon: '🤖', title: 'AI Reports', desc: 'Mistral-powered analysis generates institutional-quality reasoning for every signal.' },
    { icon: '⚡', title: 'Real-Time Delivery', desc: 'WebSocket-driven live signal feed with instant push notifications to your dashboard.' },
    { icon: '📊', title: 'Portfolio Analytics', desc: 'Track every trade, analyze performance, and optimize your risk-reward profile.' },
]
