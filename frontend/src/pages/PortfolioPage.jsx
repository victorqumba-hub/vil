import React, { useState, useEffect } from 'react';
import RiskMonitorPanel from '../components/RiskMonitorPanel';
import { getPortfolioSummary, getBrokerAccount } from '../services/api';
import './PortfolioPage.css';

const PortfolioPage = () => {
    const [portfolio, setPortfolio] = useState(null);
    const [brokerAccount, setBrokerAccount] = useState(null);
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 1024);
        window.addEventListener('resize', handleResize);

        const fetchData = async () => {
            const [pRes, bRes] = await Promise.all([
                getPortfolioSummary(),
                getBrokerAccount()
            ]);
            setPortfolio(pRes.data);
            setBrokerAccount(bRes.data);
        };
        fetchData();
        const interval = setInterval(fetchData, 5000);

        return () => {
            window.removeEventListener('resize', handleResize);
            clearInterval(interval);
        };
    }, []);

    const riskScore = portfolio?.risk_score || 25.4;

    return (
        <div className="tab-page portfolio-page container animate-in">
            <div className="risk-meter-hero glass-card">
                <div className="meter-svg-wrap">
                    <svg viewBox="0 0 100 100" className="risk-svg">
                        <circle cx="50" cy="50" r="45" className="meter-bg" />
                        <circle cx="50" cy="50" r="45" className="meter-fill" style={{
                            strokeDasharray: '283',
                            strokeDashoffset: 283 - (283 * riskScore / 100)
                        }} />
                    </svg>
                    <div className="meter-content">
                        <span className="m-val">{riskScore.toFixed(1)}%</span>
                        <span className="m-label">RISK LEVEL</span>
                    </div>
                </div>
                <div className="meter-stats">
                    <div className="m-stat">
                        <span className="l">DAILY DRAWDOWN</span>
                        <span className="v red">-0.12%</span>
                    </div>
                    <div className="m-stat" style={{ textAlign: 'right' }}>
                        <span className="l">TOTAL EXPOSURE</span>
                        <span className="v">$12,400</span>
                    </div>
                </div>
            </div>

            <div className="portfolio-analytics-stack">
                <RiskMonitorPanel
                    portfolio={portfolio}
                    brokerAccount={brokerAccount}
                    variant={isMobile ? "mobile-cards" : "desktop"}
                />
            </div>
        </div>
    );
};

export default PortfolioPage;
