import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('vil_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Auto-refresh on 401 responses
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true
            const refreshToken = localStorage.getItem('vil_refresh_token')
            if (refreshToken) {
                try {
                    const res = await axios.post(`${API_BASE}/api/auth/refresh`, {
                        refresh_token: refreshToken,
                    })
                    const { access_token, refresh_token: newRefresh } = res.data
                    localStorage.setItem('vil_token', access_token)
                    if (newRefresh) localStorage.setItem('vil_refresh_token', newRefresh)
                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshErr) {
                    // Refresh failed — force logout
                    localStorage.removeItem('vil_token')
                    localStorage.removeItem('vil_refresh_token')
                    window.location.href = '/login'
                    return Promise.reject(refreshErr)
                }
            }
        }
        return Promise.reject(error)
    }
)

// Pipeline
export const getPipelineStatus = () => api.get('/api/pipeline/status')
export const runPipeline = (params) => api.post('/api/pipeline/run', params)

// Auth
export const register = (data) => api.post('/api/register', data)
export const login = (data) => api.post('/api/login', data)
export const getMe = () => api.get('/api/me')
export const refreshToken = (data) => api.post('/api/auth/refresh', data)
export const logout = () => api.post('/api/auth/logout')
export const changePassword = (data) => api.post('/api/auth/change-password', data)
export const verifyEmail = (token) => api.get(`/api/verify-email?token=${token}`)

// Signals
export const getLiveSignals = (limit = 20, asset_class) => {
    const params = new URLSearchParams({ limit })
    if (asset_class) params.append('asset_class', asset_class)
    return api.get(`/api/signals/live?${params}`)
}
export const getHistoricalSignals = (params) => api.get('/api/signals/history', { params })
export const getSignalForensic = (signalId) => api.get(`/api/signals/${signalId}/forensic`)
export const getRegimeAttribution = (params) => api.get('/api/signals/regime-attribution', { params })

// Portfolio
export const getPortfolioSummary = () => api.get('/api/portfolio/summary')
export const getPortfolioTrades = () => api.get('/api/portfolio/trades')

// Broker (OANDA — legacy direct)
export const getBrokerAccount = () => api.get('/api/broker/account')
export const getBrokerTrades = () => api.get('/api/broker/trades')
export const getBrokerStats = () => api.get('/api/broker/stats')

// Broker Integration (per-user encrypted)
export const connectBroker = (data) => api.post('/api/broker-integration/connect', data)
export const getBrokerStatus = () => api.get('/api/broker-integration/status')
export const disconnectBroker = () => api.delete('/api/broker-integration/disconnect')
export const syncBrokerData = () => api.post('/api/broker-integration/sync')

// Admin
export const getAdminUsers = () => api.get('/api/admin/users')
export const suspendUser = (userId) => api.post(`/api/admin/users/${userId}/suspend`)
export const activateUser = (userId) => api.post(`/api/admin/users/${userId}/activate`)
export const forceLogout = (userId) => api.post(`/api/admin/users/${userId}/force-logout`)
export const disableBroker = (userId) => api.post(`/api/admin/users/${userId}/disable-broker`)
export const getAuditLogs = (limit = 100, actionType) => {
    const params = new URLSearchParams({ limit })
    if (actionType) params.append('action_type', actionType)
    return api.get(`/api/admin/audit-logs?${params}`)
}
export const getSystemHealth = () => api.get('/api/admin/system-health')

// Market data
export const getOHLCV = (params) => api.get('/api/marketdata/ohlcv', { params })
export const getAssets = () => api.get('/api/marketdata/assets')

// Reports
export const getAIReports = (limit = 20) => api.get(`/api/reports/ai?limit=${limit}`)
export const generateReport = (signalId) => api.post(`/api/reports/generate?signal_id=${signalId}`)
export const getForensicAnalysis = (signalId) => api.get(`/api/reports/forensics/analysis/${signalId}`)
export const getIntelligenceReports = (limit = 10) => api.get(`/api/reports/forensics/intelligence?limit=${limit}`)

// Non-essentials
export const getCalendar = () => api.get('/api/calendar')
export const getNews = () => api.get('/api/news')
export const getQuotes = () => api.get('/api/quotes')
export const getMarketHours = () => api.get('/api/tools/market-hours')
export const convertCurrency = (params) => api.get('/api/tools/converter', { params })

export default api

