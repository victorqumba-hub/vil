import React, { useState, useEffect } from 'react';
import LiveSignalStream from '../components/LiveSignalStream';
import { getLiveSignals } from '../services/api';
import { connectWebSocket } from '../services/ws';
import './SignalsPage.css';

const SignalsPage = () => {
    const [signals, setSignals] = useState([]);
    const [statusFilter, setStatusFilter] = useState('ACTIVE');
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 1024);
        window.addEventListener('resize', handleResize);

        const fetchSignals = async () => {
            const res = await getLiveSignals();
            setSignals(res.data);
        };
        fetchSignals();

        const cleanup = connectWebSocket('signals', (msg) => {
            if (msg.eventType === 'SIGNAL_UPDATE' || msg.eventType === 'SIGNAL_CREATED') {
                setSignals(prev => {
                    const id = msg.signalId || msg.id;
                    const exists = prev.find(s => (s.signalId || s.id) === id);
                    if (exists) {
                        return prev.map(s => (s.signalId || s.id) === id ? { ...s, ...msg } : s);
                    }
                    return [msg, ...prev].slice(0, 100);
                });
            }
        });

        return () => {
            window.removeEventListener('resize', handleResize);
            cleanup();
        };
    }, []);

    const filtered = signals.filter(s => (s.status || 'ACTIVE').toUpperCase() === statusFilter);

    const tabs = [
        { key: 'ACTIVE', label: 'Active' },
        { key: 'PENDING', label: 'Pending' },
        { key: 'COMPLETED', label: 'Closed' }
    ];

    return (
        <div className="tab-page signals-page container animate-in">
            <div className="tab-header-strip">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        className={`tab-btn ${statusFilter === tab.key ? 'active' : ''}`}
                        onClick={() => setStatusFilter(tab.key)}
                    >
                        {tab.label}
                        <span className="count">
                            {signals.filter(s => (s.status || 'ACTIVE').toUpperCase() === tab.key).length}
                        </span>
                    </button>
                ))}
            </div>

            <div className="signals-content">
                <LiveSignalStream
                    signals={filtered}
                    variant={isMobile ? "mobile-condensed" : "desktop"}
                />
            </div>
        </div>
    );
};

export default SignalsPage;
