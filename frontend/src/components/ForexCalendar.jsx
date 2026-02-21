import { useEffect, useState } from 'react'
import GlassCard from './GlassCard'
import { getCalendar } from '../services/api'
import './ForexCalendar.css'

export default function ForexCalendar() {
    const [events, setEvents] = useState([])

    useEffect(() => {
        getCalendar()
            .then(r => setEvents(r.data))
            .catch(() => setEvents(MOCK_EVENTS))
    }, [])

    const data = events.length ? events : MOCK_EVENTS

    return (
        <GlassCard title="Economic Calendar" icon="📅" className="calendar-card">
            <div className="calendar-list">
                {data.map((ev, i) => (
                    <div key={i} className="cal-row animate-in" style={{ animationDelay: `${i * 0.06}s` }}>
                        <div className="cal-time">
                            {new Date(ev.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <span className={`badge ${ev.impact}`}>{ev.currency}</span>
                        <div className="cal-event">{ev.event}</div>
                        <div className="cal-values">
                            <span className="cal-forecast">F: {ev.forecast || '—'}</span>
                            <span className="cal-prev">P: {ev.previous || '—'}</span>
                        </div>
                        <span className={`impact-dot ${ev.impact}`} />
                    </div>
                ))}
            </div>
        </GlassCard>
    )
}

const MOCK_EVENTS = [
    { time: new Date().toISOString(), currency: 'USD', event: 'Non-Farm Payrolls', impact: 'high', forecast: '185K', previous: '175K' },
    { time: new Date().toISOString(), currency: 'EUR', event: 'ECB Rate Decision', impact: 'high', forecast: '4.50%', previous: '4.50%' },
    { time: new Date().toISOString(), currency: 'GBP', event: 'CPI y/y', impact: 'high', forecast: '4.1%', previous: '4.0%' },
    { time: new Date().toISOString(), currency: 'JPY', event: 'BOJ Policy Rate', impact: 'high', forecast: '-0.10%', previous: '-0.10%' },
    { time: new Date().toISOString(), currency: 'USD', event: 'FOMC Minutes', impact: 'medium', forecast: '', previous: '' },
    { time: new Date().toISOString(), currency: 'AUD', event: 'Employment Change', impact: 'medium', forecast: '25.0K', previous: '14.6K' },
]
