import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import './AppShell.css';

const AppShell = ({ children }) => {
    const location = useLocation();
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 1024);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Hide Shell on Landing/Login/Register
    const hideShell = ['/', '/login', '/register'].includes(location.pathname);

    // On Desktop, we might want a different reveal behavior, but for now we follow the user request
    // to keep the Landing page accessible and integrated.
    if (hideShell) {
        return <div className="pwa-root landing-mode">{children}</div>;
    }

    const navItems = [
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/signals', label: 'Signals', icon: '📡' },
        { path: '/portfolio', label: 'Portfolio', icon: '💼' },
        { path: '/audit', label: 'Audit', icon: '📜' },
        { path: '/settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <div className={`app-shell ${isMobile ? 'mobile' : 'desktop'}`}>
            {/* Top Header */}
            <header className="top-header">
                <div className="header-left">
                    <div className="logo-compact">VIL</div>
                </div>
                <div className="header-center">
                    <div className="account-selector">
                        <span>Demo Account</span>
                        <span className="dropdown-arrow">▾</span>
                    </div>
                </div>
                <div className="header-right">
                    <button className="icon-btn">🔔</button>
                    <button className="icon-btn profile-btn">👤</button>
                </div>

                {/* Micro-strip indicator */}
                <div className="status-strip">
                    <span className="badge-status live">LIVE</span>
                    <span className="regime-pill">TRENDING BULLISH</span>
                    <span className="connection-pill green">OANDA OK</span>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="core-content">
                {children}
            </main>

            {/* Bottom Navigation (Mobile Only) */}
            {isMobile && (
                <nav className="bottom-nav">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{item.label}</span>
                        </NavLink>
                    ))}
                </nav>
            )}

            {/* Sidebar (Desktop Only) */}
            {!isMobile && (
                <aside className="sidebar">
                    <div className="sidebar-nav">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
                            >
                                <span className="nav-icon">{item.icon}</span>
                                <span className="nav-label">{item.label}</span>
                            </NavLink>
                        ))}
                    </div>
                </aside>
            )}
        </div>
    );
};

export default AppShell;
