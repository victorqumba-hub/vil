import { useEffect, useRef } from 'react'
import GlassCard from './GlassCard'
import './SignalChart.css'

export default function SignalChart({ symbol, candles = [], entry, stopLoss, takeProfit, direction }) {
    const containerRef = useRef(null)
    const chartRef = useRef(null)

    useEffect(() => {
        // Only render if we have the lightweight-charts library and candles
        if (!containerRef.current || candles.length === 0) return

        let chart
        let series

        const initChart = async () => {
            try {
                const { createChart } = await import('lightweight-charts')

                chart = createChart(containerRef.current, {
                    width: containerRef.current.clientWidth,
                    height: 300,
                    layout: {
                        background: { color: 'transparent' },
                        textColor: 'rgba(255,255,255,0.5)',
                        fontSize: 11,
                    },
                    grid: {
                        vertLines: { color: 'rgba(255,255,255,0.03)' },
                        horzLines: { color: 'rgba(255,255,255,0.03)' },
                    },
                    crosshair: {
                        mode: 0,
                        vertLine: { color: 'rgba(99,102,241,0.3)', width: 1 },
                        horzLine: { color: 'rgba(99,102,241,0.3)', width: 1 },
                    },
                    timeScale: {
                        borderColor: 'rgba(255,255,255,0.06)',
                        timeVisible: true,
                    },
                    rightPriceScale: {
                        borderColor: 'rgba(255,255,255,0.06)',
                    },
                })

                series = chart.addCandlestickSeries({
                    upColor: '#10b981',
                    downColor: '#ef4444',
                    borderUpColor: '#10b981',
                    borderDownColor: '#ef4444',
                    wickUpColor: '#10b981',
                    wickDownColor: '#ef4444',
                })

                const chartData = candles.map(c => ({
                    time: Math.floor(new Date(c.timestamp || c.time).getTime() / 1000),
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close,
                }))

                series.setData(chartData)

                // ── Price Lines (Entry, SL, TP) ──────────────────────────
                if (entry) {
                    series.createPriceLine({
                        price: entry,
                        color: '#6366f1',
                        lineWidth: 2,
                        lineStyle: 0,
                        axisLabelVisible: true,
                        title: 'Entry',
                    })
                }

                if (stopLoss) {
                    series.createPriceLine({
                        price: stopLoss,
                        color: '#ef4444',
                        lineWidth: 1,
                        lineStyle: 2,
                        axisLabelVisible: true,
                        title: 'SL',
                    })
                }

                if (takeProfit) {
                    series.createPriceLine({
                        price: takeProfit,
                        color: '#10b981',
                        lineWidth: 1,
                        lineStyle: 2,
                        axisLabelVisible: true,
                        title: 'TP',
                    })
                }

                chart.timeScale().fitContent()
                chartRef.current = chart

                // Resize observer
                const handleResize = () => {
                    if (containerRef.current && chart) {
                        chart.applyOptions({ width: containerRef.current.clientWidth })
                    }
                }
                window.addEventListener('resize', handleResize)

                return () => {
                    window.removeEventListener('resize', handleResize)
                }
            } catch (err) {
                console.warn('Lightweight Charts not available:', err)
            }
        }

        initChart()

        return () => {
            if (chartRef.current) {
                chartRef.current.remove()
                chartRef.current = null
            }
        }
    }, [candles, entry, stopLoss, takeProfit])

    return (
        <GlassCard
            title={symbol || 'Chart'}
            icon="📈"
            className="chart-card"
        >
            <div className="chart-meta">
                {direction && (
                    <span className={`badge ${direction?.toLowerCase()}`}>{direction}</span>
                )}
                {entry && <span className="chart-level entry">Entry: {entry}</span>}
                {stopLoss && <span className="chart-level sl">SL: {stopLoss}</span>}
                {takeProfit && <span className="chart-level tp">TP: {takeProfit}</span>}
            </div>
            <div ref={containerRef} className="chart-container">
                {candles.length === 0 && (
                    <div className="chart-placeholder">
                        <span>📊</span>
                        <p>Chart data loading...</p>
                    </div>
                )}
            </div>
        </GlassCard>
    )
}
