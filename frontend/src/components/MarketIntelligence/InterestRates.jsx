import '../GlassCard.css'

export default function InterestRates() {
    const RATES = [
        { bank: 'FED', current: '5.50%', next: 'Mar 20, 2024' },
        { bank: 'ECB', current: '4.50%', next: 'Mar 07, 2024' },
        { bank: 'BOE', current: '5.25%', next: 'Mar 21, 2024' },
        { bank: 'BOJ', current: '-0.10%', next: 'Mar 19, 2024' },
        { bank: 'RBA', current: '4.35%', next: 'Mar 19, 2024' },
    ]

    return (
        <div className="glass-card">
            <div className="card-header">
                <h3 className="card-title">Central Bank Interest Rates</h3>
            </div>
            <div className="card-content no-padding">
                <table className="dark-table simple-table">
                    <thead>
                        <tr>
                            <th>Bank</th>
                            <th>Current</th>
                            <th className="text-right">Next Meeting</th>
                        </tr>
                    </thead>
                    <tbody>
                        {RATES.map((r, i) => (
                            <tr key={i}>
                                <td><b className="text-white">{r.bank}</b></td>
                                <td>{r.current}</td>
                                <td className="text-right text-muted">{r.next}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
