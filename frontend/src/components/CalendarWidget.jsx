import { useState, useEffect } from 'react'
import GlassCard from './GlassCard'
import { getCalendar } from '../services/api'
import './CalendarWidget.css'

export default function CalendarWidget() {
    const [events, setEvents] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        getCalendar()
            .then(res => {
                setEvents(res.data)
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to fetch calendar:", err)
                setLoading(false)
            })
    }, [])

    return (
        <GlassCard title="Economic Calendar" icon="📅" className="calendar-card">
            <div className="calendar-list">
                {loading ? (
                    <div className="loading-spinner-inline" />
                ) : events.length > 0 ? (
                    events.map((evt, i) => (
                        <div key={i} className="calendar-row">
                            <div className="cal-time-col">
                                <span className="cal-time">{new Date(evt.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                <span className={`cal-impact ${evt.impact}`}>{evt.impact}</span>
                            </div>
                            <div className="cal-info-col">
                                <div className="cal-currency">{evt.currency}</div>
                                <div className="cal-event">{evt.event}</div>
                            </div>
                            <div className="cal-data-col">
                                <div className="cal-actual">{evt.actual || '-'}</div>
                                <div className="cal-forecast" title="Forecast">{evt.forecast}</div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="no-data">No upcoming events</div>
                )}
            </div>
        </GlassCard>
    )
}
