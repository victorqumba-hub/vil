import GlassCard from './GlassCard'
import './AIReportPanel.css'

export default function AIReportPanel({ reports = [] }) {
    if (!reports.length) {
        return (
            <GlassCard title="AI Reports" icon="🤖">
                <p className="no-data">No AI reports generated yet. Reports will appear here after signal analysis.</p>
            </GlassCard>
        )
    }

    return (
        <GlassCard title="AI Reports" icon="🤖">
            <div className="reports-list">
                {reports.map((r, i) => (
                    <div key={i} className="report-item">
                        <div className="report-header">
                            <span className="report-symbol">{r.symbol}</span>
                            <time className="report-time">{new Date(r.timestamp).toLocaleString()}</time>
                        </div>
                        <p className="report-summary">{r.summary}</p>
                        {r.rationale && <p className="report-rationale">{r.rationale}</p>}
                        {r.risk_assessment && <p className="report-risk">{r.risk_assessment}</p>}
                    </div>
                ))}
            </div>
        </GlassCard>
    )
}
