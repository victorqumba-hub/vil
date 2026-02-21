import { useState, useEffect } from 'react'
import GlassCard from './GlassCard'
import { getNews } from '../services/api'
import './NewsWidget.css'

export default function NewsWidget() {
    const [news, setNews] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        getNews()
            .then(res => {
                setNews(res.data)
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to fetch news:", err)
                setLoading(false)
            })
    }, [])

    return (
        <GlassCard title="Market News" icon="📰" className="news-card">
            <div className="news-list">
                {loading ? (
                    <div className="loading-spinner-inline" />
                ) : news.length > 0 ? (
                    news.map((item, i) => (
                        <div key={i} className="news-item">
                            <div className="news-header">
                                <span className={`news-tag ${item.category}`}>{item.category}</span>
                                <span className="news-time">{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                            <a href={item.url} target="_blank" rel="noreferrer" className="news-title">
                                {item.title}
                            </a>
                            <div className="news-source">{item.source}</div>
                        </div>
                    ))
                ) : (
                    <div className="no-data">No news available</div>
                )}
            </div>
        </GlassCard>
    )
}
