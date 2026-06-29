import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Tenants from './pages/Tenants'
import Incidents from './pages/Incidents'
import Vulnerabilities from './pages/Vulnerabilities'
import ThreatIntel from './pages/ThreatIntel'
import Reports from './pages/Reports'
import SigmaRules from './pages/SigmaRules'
import Scanner from './pages/Scanner'
import Placeholder from './pages/Placeholder'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-sovereign-dark">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tenants" element={<Tenants />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/vulnerabilities" element={<Vulnerabilities />} />
            <Route path="/threat-intel" element={<ThreatIntel />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/sigma-rules" element={<SigmaRules />} />
            <Route path="/scanner" element={<Scanner />} />
            <Route path="*" element={<Placeholder />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
