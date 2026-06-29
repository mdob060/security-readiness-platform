import { useEffect, useState } from 'react'
import api from '../api/client'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { Shield, AlertTriangle, Users, Activity, Eye, Database, TrendingUp, Zap } from 'lucide-react'

const SEVERITY_COLORS = { critical: '#ff3b6b', high: '#ff6b35', medium: '#ffd700', low: '#00d4ff' }

function StatCard({ title, value, icon: Icon, color, sub }) {
  return (
    <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5 hover:border-sovereign-cyan/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg`} style={{ background: `${color}15` }}>
          <Icon size={20} style={{ color }} />
        </div>
        <span className="text-xs text-slate-500">{sub}</span>
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-slate-400">{title}</div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [activity, setActivity] = useState([])
  const [recentIncidents, setRecentIncidents] = useState([])
  const [riskBySector, setRiskBySector] = useState([])
  const [vulnSummary, setVulnSummary] = useState({})

  useEffect(() => {
    api.get('/dashboard/stats').then(r => setStats(r.data)).catch(() => {})
    api.get('/dashboard/threat-activity').then(r => setActivity(r.data)).catch(() => {})
    api.get('/dashboard/recent-incidents').then(r => setRecentIncidents(r.data)).catch(() => {})
    api.get('/dashboard/risk-by-sector').then(r => setRiskBySector(r.data)).catch(() => {})
    api.get('/dashboard/vulnerability-summary').then(r => setVulnSummary(r.data)).catch(() => {})
  }, [])

  const pieData = Object.entries(vulnSummary).map(([k, v]) => ({ name: k, value: v }))

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">لوحة التحكم</h1>
          <p className="text-slate-400 text-sm mt-1">مراقبة حية لجميع العمليات الأمنية</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-sovereign-green">
          <div className="w-2 h-2 rounded-full bg-sovereign-green animate-pulse" />
          تحديث مباشر
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard title="إجمالي العملاء" value={stats?.total_tenants ?? '—'} icon={Users} color="#00d4ff" sub="ليبيا" />
        <StatCard title="حوادث نشطة" value={stats?.active_incidents ?? '—'} icon={AlertTriangle} color="#ff3b6b" sub="مفتوحة" />
        <StatCard title="ثغرات حرجة" value={stats?.critical_vulns ?? '—'} icon={Shield} color="#ff6b35" sub="تتطلب معالجة" />
        <StatCard title="تهديدات محجوبة" value={stats?.threats_blocked ?? '—'} icon={Activity} color="#00ff88" sub="هذا الشهر" />
        <StatCard title="إجمالي الأصول" value={stats?.total_assets ?? '—'} icon={Database} color="#a78bfa" sub="مراقبة" />
        <StatCard title="قواعد Sigma" value={stats?.active_sigma_rules ?? '—'} icon={Eye} color="#ffd700" sub="مفعّلة" />
        <StatCard title="مؤشرات التهديد" value={stats?.total_iocs ?? '—'} icon={TrendingUp} color="#f472b6" sub="IOC نشط" />
        <StatCard title="متوسط درجة المخاطر" value={`${stats?.avg_risk_score ?? '—'}%`} icon={Zap} color="#fb923c" sub="عبر العملاء" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Threat Activity */}
        <div className="col-span-2 bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">نشاط التهديدات - 30 يوم</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={activity}>
              <defs>
                <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff3b6b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff3b6b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e2d4a', borderRadius: 8 }} />
              <Area type="monotone" dataKey="threats" stroke="#00d4ff" fill="url(#cyanGrad)" name="تهديدات" />
              <Area type="monotone" dataKey="blocked" stroke="#00ff88" fill="url(#redGrad)" name="محجوبة" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Vuln Pie */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">الثغرات حسب الخطورة</h3>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={SEVERITY_COLORS[entry.name] || '#64748b'} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e2d4a', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-1 text-xs text-slate-400">
                <div className="w-2 h-2 rounded-full" style={{ background: SEVERITY_COLORS[d.name] }} />
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Recent Incidents */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">آخر الحوادث</h3>
          <div className="space-y-3">
            {recentIncidents.map(inc => (
              <div key={inc.id} className="flex items-start justify-between py-2 border-b border-sovereign-border/50 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{inc.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{inc.tenant}</div>
                </div>
                <span className={`badge-${inc.severity} mr-2 flex-shrink-0`}>{inc.severity}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk by Sector */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">المخاطر حسب القطاع</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={riskBySector} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} domain={[0, 100]} />
              <YAxis dataKey="sector" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={60} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e2d4a', borderRadius: 8 }} />
              <Bar dataKey="avg_risk" fill="#00d4ff" radius={[0, 4, 4, 0]} name="متوسط المخاطر" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
