import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Activity, Brain, Shield, AlertTriangle,
  Crosshair, Eye, Radio, Filter, Mail, Scan,
  Search, Database, Network, Building2, Zap, TrendingUp,
  FileText, Users, Settings, ChevronRight, Wifi
} from 'lucide-react'

const REAL_BADGE = () => (
  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border border-sovereign-cyan/50 text-sovereign-cyan bg-sovereign-cyan/10">
    REAL
  </span>
)

const Section = ({ title, children }) => (
  <div className="mb-4">
    <div className="text-[10px] font-bold text-slate-500 tracking-widest uppercase px-3 mb-1">{title}</div>
    {children}
  </div>
)

const NavItem = ({ to, icon: Icon, label, isReal }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200 cursor-pointer ${
        isActive
          ? 'text-sovereign-cyan bg-sovereign-border'
          : 'text-slate-400 hover:text-sovereign-cyan hover:bg-sovereign-border/50'
      }`
    }
  >
    <Icon size={15} />
    <span className="flex-1">{label}</span>
    {isReal && <REAL_BADGE />}
  </NavLink>
)

export default function Sidebar() {
  return (
    <aside className="w-56 bg-sovereign-navy border-l border-sovereign-border flex flex-col min-h-screen">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-sovereign-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sovereign-cyan/30 to-blue-600/30 border border-sovereign-cyan/40 flex items-center justify-center">
            <Shield size={16} className="text-sovereign-cyan" />
          </div>
          <div>
            <div className="text-xs font-bold text-sovereign-cyan leading-tight">SOVEREIGN</div>
            <div className="text-[9px] text-slate-500 leading-tight">SECURITY PLATFORM</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 overflow-y-auto space-y-1">
        <Section title="OVERVIEW">
          <NavItem to="/" icon={LayoutDashboard} label="Dashboard" isReal />
          <NavItem to="/live-pipeline" icon={Activity} label="Live Pipeline" isReal />
          <NavItem to="/ai-brain" icon={Brain} label="AI Brain" />
        </Section>

        <Section title="LIVE OPERATIONS">
          <NavItem to="/soc" icon={Shield} label="SOC Center" isReal />
          <NavItem to="/incidents" icon={AlertTriangle} label="Incidents" isReal />
          <NavItem to="/red-team" icon={Crosshair} label="Red Team" isReal />
          <NavItem to="/blue-team" icon={Eye} label="Blue Team" isReal />
          <NavItem to="/honeypot" icon={Radio} label="Honeypot" isReal />
          <NavItem to="/sigma-rules" icon={Filter} label="Sigma Rules" isReal />
          <NavItem to="/phishing-sim" icon={Mail} label="Phishing Sim" isReal />
          <NavItem to="/scanner" icon={Scan} label="Scan Scope" isReal />
        </Section>

        <Section title="INTELLIGENCE & HUNTING">
          <NavItem to="/threat-hunting" icon={Search} label="Threat Hunting" isReal />
          <NavItem to="/threat-intel" icon={Database} label="Threat Intel" isReal />
          <NavItem to="/federation" icon={Network} label="Federation" />
        </Section>

        <Section title="SPECIALIZED MODULES">
          <NavItem to="/banking" icon={Building2} label="Banking" isReal />
          <NavItem to="/ot-scada" icon={Zap} label="OT/SCADA" isReal />
          <NavItem to="/ueba" icon={TrendingUp} label="UEBA" isReal />
          <NavItem to="/vulnerabilities" icon={AlertTriangle} label="Vulnerabilities" isReal />
          <NavItem to="/grc" icon={Settings} label="GRC" />
        </Section>

        <Section title="MANAGEMENT">
          <NavItem to="/tenants" icon={Users} label="Tenants" isReal />
          <NavItem to="/automation" icon={Zap} label="Automation" />
          <NavItem to="/analytics" icon={TrendingUp} label="Analytics" />
          <NavItem to="/reports" icon={FileText} label="Reports" isReal />
        </Section>
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-sovereign-border">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-sovereign-green animate-pulse" />
          <span className="text-xs text-slate-500">All Systems Operational</span>
        </div>
      </div>
    </aside>
  )
}
