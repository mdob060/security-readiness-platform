import { useEffect, useState } from 'react'
import api from '../api/client'
import { Users, Search, Filter, Plus, ExternalLink, AlertTriangle, Shield } from 'lucide-react'

const INDUSTRY_COLORS = {
  Banking: 'text-yellow-400 bg-yellow-900/30 border-yellow-800',
  Government: 'text-blue-400 bg-blue-900/30 border-blue-800',
  Telecom: 'text-purple-400 bg-purple-900/30 border-purple-800',
  Energy: 'text-red-400 bg-red-900/30 border-red-800',
  Aviation: 'text-cyan-400 bg-cyan-900/30 border-cyan-800',
  Media: 'text-pink-400 bg-pink-900/30 border-pink-800',
  Education: 'text-green-400 bg-green-900/30 border-green-800',
}

function RiskBar({ score }) {
  const color = score >= 85 ? '#ff3b6b' : score >= 70 ? '#ff6b35' : score >= 50 ? '#ffd700' : '#00ff88'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-sovereign-border rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-xs font-bold w-8" style={{ color }}>{score}</span>
    </div>
  )
}

export default function Tenants() {
  const [tenants, setTenants] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/tenants/').then(r => { setTenants(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const industries = ['all', ...new Set(tenants.map(t => t.industry).filter(Boolean))]
  const filtered = tenants.filter(t => {
    const matchSearch = t.name.includes(search) || t.domain.includes(search)
    const matchFilter = filter === 'all' || t.industry === filter
    return matchSearch && matchFilter
  })

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">العملاء</h1>
          <p className="text-slate-400 text-sm mt-1">المؤسسات الليبية المحمية ({tenants.length} عميل)</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sovereign-cyan text-sovereign-dark font-semibold text-sm hover:bg-sovereign-cyan/90 transition-colors">
          <Plus size={16} />
          إضافة عميل
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            className="w-full bg-sovereign-panel border border-sovereign-border rounded-lg pr-9 pl-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovereign-cyan/50"
            placeholder="بحث بالاسم أو النطاق..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {industries.map(ind => (
            <button
              key={ind}
              onClick={() => setFilter(ind)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                filter === ind
                  ? 'bg-sovereign-cyan text-sovereign-dark'
                  : 'bg-sovereign-panel border border-sovereign-border text-slate-400 hover:border-sovereign-cyan/30'
              }`}
            >
              {ind === 'all' ? 'الكل' : ind}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-20 text-slate-500">جارٍ التحميل...</div>
      ) : (
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sovereign-border">
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">المؤسسة</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">النطاق</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">القطاع</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">درجة المخاطر</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الثغرات</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الحوادث</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الحالة</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id} className="border-b border-sovereign-border/50 hover:bg-sovereign-border/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-sm text-white">{t.name}</div>
                  </td>
                  <td className="px-4 py-3">
                    <a
                      href={`https://${t.domain}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1 text-xs text-sovereign-cyan hover:underline"
                    >
                      {t.domain} <ExternalLink size={11} />
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs border ${INDUSTRY_COLORS[t.industry] || 'text-slate-400 bg-slate-800 border-slate-700'}`}>
                      {t.industry}
                    </span>
                  </td>
                  <td className="px-4 py-3 w-36">
                    <RiskBar score={t.risk_score} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-bold ${t.open_vulns > 0 ? 'text-red-400' : 'text-slate-500'}`}>
                      {t.open_vulns}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-bold ${t.active_incidents > 0 ? 'text-yellow-400' : 'text-slate-500'}`}>
                      {t.active_incidents}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1 text-xs text-sovereign-green">
                      <div className="w-1.5 h-1.5 rounded-full bg-sovereign-green animate-pulse" />
                      نشط
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
