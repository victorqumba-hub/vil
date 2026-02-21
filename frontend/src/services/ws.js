const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`

export function connectWebSocket(channel, onMessage) {
    const url = `${WS_BASE}/ws/${channel}`
    let ws = null
    let reconnectTimeout = null

    function connect() {
        ws = new WebSocket(url)

        ws.onopen = () => console.log(`[WS] Connected to ${channel}`)

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                onMessage(data)
            } catch (e) {
                console.error('[WS] Parse error:', e)
            }
        }

        ws.onclose = () => {
            console.log(`[WS] Disconnected from ${channel}, reconnecting...`)
            reconnectTimeout = setTimeout(connect, 3000)
        }

        ws.onerror = (err) => console.error(`[WS] Error on ${channel}:`, err)
    }

    connect()

    return () => {
        clearTimeout(reconnectTimeout)
        if (ws) ws.close()
    }
}
