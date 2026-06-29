import { useState, useEffect } from 'react'
import api from '../api/client'
import { Scan, Play, Clock, AlertTriangle, CheckCircle, Info } from 'lucide-react'

const SEVERITY_ICON = { critical: '🔴', high: '🟠', medium: '🟡', low: '🔵', info: '⚪' }

export default function Scanner() {
  const [target, setTarget] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [tenants, setTenants] = useState([])
  const [scanning, setScanning] = useState(false)
  const [scanId, setScanId] = useState(null)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    api.get('/tenants/').then(r => setTenants(r.data)).catch(() => {})
    api.get('/scanner/history').then(r => setHistory(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!scanId) return
    const interval = setInterval(() => {
      api.get(`/scanner/results/${scanId}`).then(r => {
        if (r.data.status === 'completed') {
          setResult(r.data)
          setScanning(false)
          clearInterval(interval)
          api.get('/scanner/history').then(hr => setHistory(hr.data)).catch(() => {})
        }
      })
    }, 2000)
    return () => clearInterval(interval)
  }, [scanId])

  const startScan = () => {
    if (!target.trim()) return
    setScanning(true)
    setResult(null)
    api.post('/scanner/scan', {
      target: target.trim(),
      scan_type: 'basic',
      tenant_id: tenantId ? parseInt(tenantId) : null,
    }).then(r => {
      setScanId(r.data.scan_id)
    }).catch(() => setScanning(false))
  }

  const RISK_COLORS = { critical: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-blue-400' }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">فحص الأهداف</h1>
        <p className="text-slate-400 text-sm mt-1">فحص الثغرات وتحليل الأمن للمواقع المرخصة</p>
      </div>

      {/* Scan Form */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5 mb-5">
        <h3 className="text-sm font-semibold text-white mb-4">إعداد الفحص</h3>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="col-span-2">
            <label className="text-xs text-slate-400 mb-1 block">الهدف (نطاق أو IP)</label>
            <input
              className="w-full bg-sovereign-blue border border-sovereign-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovereign-cyan/50 font-mono"
              placeholder="example.com أو https://example.com"
              value={target}
              onChange={e => setTarget(e.target.value)}
              dir="ltr"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">العميل (اختياري)</label>
            <select
              className="w-full bg-sovereign-blue border border-sovereign-border rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sovereign-cyan/50"
              value={tenantId}
              onChange={e => setTenantId(e.target.value)}
            >
              <option value="">غير محدد</option>
              {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
        </div>

        {/* Scan Types */}
        <div className="flex gap-2 mb-4">
          {['فحص أساسي', 'HTTP Headers', 'SSL/TLS', 'DNS'].map(type => (
            <span key={type} className="px-3 py-1 rounded-lg bg-sovereign-blue border border-sovereign-border text-xs text-slate-400">
              {type}
            </span>
          ))}
        </div>

        <button
          onClick={startScan}
          disabled={scanning || !target.trim()}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-sovereign-cyan text-sovereign-dark font-bold text-sm hover:bg-sovereign-cyan/90 transition-colors disabled:opacity-50"
        >
          {scanning ? (
            <>
              <div className="w-4 h-4 border-2 border-sovereign-dark border-t-transparent rounded-full animate-spin" />
              جارٍ الفحص...
            </>
          ) : (
            <>
              <Play size={16} />
              بدء الفحص
            </>
          )}
        </button>
      </div>

      {/* Scan Result */}
      {result && (
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5 mb-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">نتائج الفحص</h3>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-bold ${RISK_COLORS[result.risk_level] || 'text-slate-400'}`}>
                مستوى المخاطر: {result.risk_level}
              </span>
              <CheckCircle size={16} className="text-sovereign-green" />
            </div>
          </div>

          {result.findings?.length === 0 ? (
            <div className="text-center py-8 text-sovereign-green">
              <CheckCircle size={32} className="mx-auto mb-2" />
              <p className="text-sm">لم يتم اكتشاف ثغرات</p>
            </div>
          ) : (
            <div className="space-y-2">
              {result.findings?.map((f, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-sovereign-dark/50 border border-sovereign-border/50">
                  <span className="text-lg flex-shrink-0">{SEVERITY_ICON[f.severity] || '⚪'}</span>
                  <div>
                    <div className="text-sm text-white">{f.message}</div>
                    {f.header && <div className="text-xs text-slate-500 mt-0.5 font-mono" dir="ltr">{f.header}</div>}
                    <div className="text-xs text-slate-500 mt-0.5">{f.type}</div>
                  </div>
                  <span className={`mr-auto flex-shrink-0 badge-${f.severity}`}>{f.severity}</span>
                </div>
              ))}
            </div>
          )}

          {result.raw_output?.ssl && (
            <div className="mt-4 p-3 rounded-lg bg-sovereign-dark/50 border border-sovereign-border/50">
              <div className="text-xs text-slate-400 mb-1">معلومات SSL</div>
              <div className="text-xs text-slate-300 space-y-1">
                <div>SSL: {result.raw_output.ssl.has_ssl ? <span className="text-sovereign-green">نعم</span> : <span className="text-red-400">لا</span>}</div>
                {result.raw_output.ssl.issuer && <div>الجهة المصدرة: {result.raw_output.ssl.issuer}</div>}
                {result.raw_output.ssl.expiry && <div dir="ltr">تاريخ الانتهاء: {result.raw_output.ssl.expiry}</div>}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scan History */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">سجل الفحوصات</h3>
        {history.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">لا توجد فحوصات سابقة</div>
        ) : (
          <div className="space-y-2">
            {history.map(h => (
              <div key={h.id} className="flex items-center justify-between p-3 rounded-lg bg-sovereign-dark/30 border border-sovereign-border/30">
                <div className="flex items-center gap-3">
                  <Clock size={14} className="text-slate-500" />
                  <span className="text-xs text-slate-400">{h.scan_type}</span>
                  <span className={`badge-${h.risk_level || 'low'}`}>{h.risk_level || 'low'}</span>
                </div>
                <span className={`text-xs ${h.status === 'completed' ? 'text-sovereign-green' : 'text-yellow-400'}`}>
                  {h.status === 'completed' ? 'مكتمل' : 'جارٍ'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
