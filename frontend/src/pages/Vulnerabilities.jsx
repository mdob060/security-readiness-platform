import { useEffect, useState } from 'react'
import api from '../api/client'
import { Shield, CheckCircle, AlertTriangle } from 'lucide-react'

export default function Vulnerabilities() {
  const [vulns, setVulns] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/vulnerabilities/').then(r => { setVulns(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const remediate = (id) => {
    api.patch(`/vulnerabilities/${id}/remediate`).then(() => {
      setVulns(prev => prev.map(v => v.id === id ? { ...v, status: 'remediated' } : v))
    })
  }

  const filtered = filter === 'all' ? vulns : vulns.filter(v => v.severity === filter)

  const CVSS_COLOR = (score) => {
    if (score >= 9) return '#ff3b6b'
    if (score >= 7) return '#ff6b35'
    if (score >= 4) return '#ffd700'
    return '#00d4ff'
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">الثغرات الأمنية</h1>
          <p className="text-slate-400 text-sm mt-1">{vulns.filter(v => v.status === 'open').length} ثغرة مفتوحة</p>
        </div>
      </div>

      {/* Severity Filter */}
      <div className="flex gap-2 mb-5">
        {[['all', 'الكل'], ['critical', 'حرجة'], ['high', 'عالية'], ['medium', 'متوسطة'], ['low', 'منخفضة']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setFilter(val)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === val
                ? 'bg-sovereign-cyan text-sovereign-dark'
                : 'bg-sovereign-panel border border-sovereign-border text-slate-400 hover:border-sovereign-cyan/30'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-500">جارٍ التحميل...</div>
      ) : (
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sovereign-border">
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">CVE</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الثغرة</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الخطورة</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">CVSS</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">العميل</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الحالة</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">إجراء</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(v => (
                <tr key={v.id} className="border-b border-sovereign-border/50 hover:bg-sovereign-border/20 transition-colors">
                  <td className="px-4 py-3">
                    <span className="text-xs font-mono text-sovereign-cyan">{v.cve_id || 'N/A'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-white font-medium">{v.title}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{v.affected_component}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge-${v.severity}`}>{v.severity}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-bold" style={{ color: CVSS_COLOR(v.cvss_score) }}>
                      {v.cvss_score?.toFixed(1) || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-slate-400">{v.tenant_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={v.status === 'open' ? 'badge-open' : 'badge-resolved'}>
                      {v.status === 'open' ? 'مفتوحة' : 'معالجة'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {v.status === 'open' && (
                      <button
                        onClick={() => remediate(v.id)}
                        className="flex items-center gap-1 text-xs text-sovereign-green hover:underline"
                      >
                        <CheckCircle size={13} />
                        معالجة
                      </button>
                    )}
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
