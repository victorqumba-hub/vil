import React from 'react';
import AuditPanel from '../components/AuditPanel';

const AuditPage = () => {
    return (
        <div className="tab-page audit-page">
            <header className="page-header-mobile">
                <h1 className="page-title-mobile">Performance Audit</h1>
                <p className="page-desc-mobile">Traceable institutional verification log</p>
            </header>

            <AuditPanel />

            <style dangerouslySetInnerHTML={{
                __html: `
                .page-header-mobile {
                    margin-bottom: 24px;
                }
                .page-title-mobile {
                    font-size: 1.5rem;
                    font-weight: 800;
                    font-family: var(--font-display);
                    margin-bottom: 4px;
                }
                .page-desc-mobile {
                    font-size: 0.8125rem;
                    color: var(--text-muted);
                }
            `}} />
        </div>
    );
};

export default AuditPage;
