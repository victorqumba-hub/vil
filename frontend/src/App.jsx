import { Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import ConnectBroker from './pages/ConnectBroker'
import Dashboard from './pages/Dashboard'
import SignalsPage from './pages/SignalsPage'
import PortfolioPage from './pages/PortfolioPage'
import AuditPage from './pages/AuditPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/connect-broker" element={<ConnectBroker />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/signals" element={<SignalsPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  )
}
