import React from 'react';
import './MobileAccountCard.css';

const MobileAccountCard = ({ data }) => {
    // Fallback data if none provided or missing fields
    const stats = (data && Object.keys(data).length > 0) ? {
        balance: data.balance ?? 12540.50,
        equity: data.equity ?? 12890.75,
        todayPL: data.todayPL ?? 350.25,
        marginUsed: data.marginUsed ?? 1200.00,
        freeMargin: data.freeMargin ?? 11690.75,
        riskActive: data.riskActive ?? 1.5
    } : {
        balance: 12540.50,
        equity: 12890.75,
        todayPL: 350.25,
        marginUsed: 1200.00,
        freeMargin: 11690.75,
        riskActive: 1.5
    };

    const isProfit = stats.todayPL >= 0;

    return (
        <div className="mobile-account-card glass-card">
            <div className="card-header">
                <span className="label">Total Equity</span>
                <span className={`pl-badge ${isProfit ? 'profit' : 'loss'}`}>
                    {isProfit ? '+' : ''}{stats.todayPL.toFixed(2)} Today
                </span>
            </div>

            <div className="main-stat">
                <span className="currency">$</span>
                <span className="amount">{stats.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>

            <div className="stats-grid">
                <div className="stat-item">
                    <span className="stat-label">Balance</span>
                    <span className="stat-value">${stats.balance.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Margin Used</span>
                    <span className="stat-value">${stats.marginUsed.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Free Margin</span>
                    <span className="stat-value">${stats.freeMargin.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Risk Active</span>
                    <span className="stat-value risk">{stats.riskActive}%</span>
                </div>
            </div>

            <div className="risk-bar-container">
                <div className="risk-bar-fill" style={{ width: `${Math.min(stats.riskActive * 10, 100)}%` }}></div>
            </div>
        </div>
    );
};

export default MobileAccountCard;
