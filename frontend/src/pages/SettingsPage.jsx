import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SettingsPage.css';

const SettingsPage = () => {
    const nav = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('vil_token');
        localStorage.removeItem('vil_refresh_token');
        nav('/');
    };

    const sections = [
        {
            title: 'Account Settings',
            items: [
                { label: 'Profile Information', icon: '👤' },
                { label: 'Subscription Plan', icon: '💎', detail: 'Pro Member' },
                { label: 'Security & Password', icon: '🔒' }
            ]
        },
        {
            title: 'Broker Connection',
            items: [
                { label: 'OANDA API Configuration', icon: '🔌', detail: 'Connected' },
                { label: 'Trade Execution Rules', icon: '⚡' }
            ]
        },
        {
            title: 'Platform Preferences',
            items: [
                { label: 'Dark Mode', icon: '🌙', toggle: true },
                { label: 'Push Notifications', icon: '🔔', toggle: true },
                { label: 'Sound Alerts', icon: '🔊', toggle: false }
            ]
        }
    ];

    return (
        <div className="tab-page settings-page container animate-in">
            <div className="settings-sections">
                {sections.map(section => (
                    <div key={section.title} className="settings-section">
                        <h3 className="settings-section-title">{section.title}</h3>
                        <div className="settings-list glass-card">
                            {section.items.map((item, i) => (
                                <div key={item.label} className="settings-item">
                                    <div className="item-main">
                                        <span className="item-icon">{item.icon}</span>
                                        <span className="item-label">{item.label}</span>
                                    </div>
                                    <div className="item-action">
                                        {item.detail && <span className="item-detail">{item.detail}</span>}
                                        {item.toggle !== undefined ? (
                                            <div className={`toggle-switch ${item.toggle ? 'on' : ''}`}></div>
                                        ) : (
                                            <span className="arrow">➔</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <button className="btn-logout" onClick={handleLogout}>
                Sign Out of VIL
            </button>
        </div>
    );
};

export default SettingsPage;
