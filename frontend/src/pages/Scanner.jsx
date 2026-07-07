import { useState, useEffect } from 'react'
import api from '../api/client'
import { Play, Clock, CheckCircle, Terminal, Cpu, Wifi, Shield, Globe, Search } from 'lucide-react'

const SEV_ICON = { critical: '🔴', high: '🟠', medium: '🟡', low: '🔵', info: '⚪' }
const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

const SCAN_TYPES = [
  { id: 'basic',  label: 'Basic',  desc: 'Headers + SSL + DNS',           icon: Globe  },
  { id: 'nmap',   label: 'Nmap',   desc: 'Port scan + Service detection',  icon: Wifi   },
  { id: 'web',    label: 'Web',    desc: 'Nikto + WhatWeb + WAF',          icon: Search },
  { id: 'full',   label: 'Full',   desc: 'كل الأدوات مجتمعة',              icon: Cpu    },
]

function ToolBadge({ name, info }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${info?.installed ? 'border-sovereign-green/40 bg-sovereign-green/5' : 'border-red-800/40 bg-red-900/5'}`}>
      <div className={`w-2 h-2 rounded-full ${info?.installed ? 'bg-sovereign-green' : 'bg-red-500'}`} />
      <span className="text-xs font-mono font-bold text-white">{name}</span>
      <span className={`text-[10px] ${info?.installed ? 'text-sovereign-green' : 'text-red-400'}`}>
        {info?.installed ? '✓' : '✗'}
      </span>
    </div>
  )
}

export default function Scanner() {
  const [target, setTarget]     = useState('')
  const [tenantId, setTenantId] = useState('')
  const [scanType, setScanType] = useState('basic')
  const [tenants, setTenants]   = useState([])
  const [tools, setTools]       = useState({})
  const [scanning, setScanning] = useState(false)
  const [scanId, setScanId]     = useState(null)
  const [result, setResult]     = useState(null)
  const [history, setHistory]   = useState([])
  const [activeTab, setActiveTab] = useState('findings')

  useEffect(() => {
    api.get('/tenants/').then(r => setTenants(r.data)).catch(() => {})
    api.get('/scanner/history').then(r => setHistory(r.data)).catch(() => {})
    api.get('/scanner/tools-status').then(r => setTools(r.data)).catch(() => {})
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
    setScanId(null)
    api.post('/scanner/scan', {
      target: target.trim(),
      scan_type: scanType,
      tenant_id: tenantId ? parseInt(tenantId) : null,
    }).then(r => setScanId(r.data.scan_id)).catch(() => setScanning(false))
  }

  const installedCount = Object.values(tools).filter(t => t?.installed).length
  const findings = result?.findings || []
  const criticalCount = findings.filter(f => f.severity === 'critical').length
  const highCount = findings.filter(f => f.severity === 'high').length

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Scan Scope</h1>
          <p className="text-slate-400 text-sm mt-1">محرك الفحص المتكامل مع أدوات Kali Linux</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Terminal size={14} className="text-sovereign-cyan" />
          <span className="text-sovereign-cyan font-mono">{installedCount}/{Object.keys(tools).length} أدوات مثبّتة</span>
        </div>
      </div>

      {/* Kali Tools Status */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-4 mb-5">
        <div className="flex items-center gap-2 mb-3">
          <Terminal size={14} className="text-sovereign-cyan" />
          <span className="text-xs font-semibold text-white">حالة أدوات Kali Linux</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(tools).map(([name, info]) => (
            <ToolBadge key={name} name={name} info={info} />
          ))}
        </div>
      </div>

      {/* Scan Config */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5 mb-5">
        <h3 className="text-sm font-semibold text-white mb-4">إعداد الفحص</h3>

        {/* Target Input */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="col-span-2">
            <label className="text-xs text-slate-400 mb-1 block">الهدف (Domain / IP / URL)</label>
            <input
              className="w-full bg-sovereign-blue border border-sovereign-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovereign-cyan/50 font-mono"
              placeholder="example.com  أو  192.168.1.1  أو  https://example.com"
              value={target}
              onChange={e => setTarget(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && startScan()}
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
              <option value="">غير مرتبط بعميل</option>
              {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
        </div>

        {/* Scan Type Selection */}
        <div className="mb-4">
          <label className="text-xs text-slate-400 mb-2 block">نوع الفحص</label>
          <div className="grid grid-cols-4 gap-2">
            {SCAN_TYPES.map(({ id, label, desc, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setScanType(id)}
                className={`p-3 rounded-lg border text-right transition-all ${
                  scanType === id
                    ? 'border-sovereign-cyan bg-sovereign-cyan/10 text-sovereign-cyan'
                    : 'border-sovereign-border text-slate-400 hover:border-sovereign-cyan/30'
                }`}
              >
                <Icon size={16} className="mb-2" />
                <div className="text-xs font-bold">{label}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Scan Tools for selected type */}
        <div className="mb-4 p-3 rounded-lg bg-sovereign-dark/50 border border-sovereign-border/50">
          <div className="text-[10px] text-slate-500 mb-1">الأدوات التي ستُستخدم:</div>
          <div className="flex flex-wrap gap-2">
            {scanType === 'basic'  && ['whois', 'dig', 'curl', 'wafw00f', 'whatweb'].map(t => <span key={t} className="text-xs font-mono text-sovereign-cyan">{t}</span>)}
            {scanType === 'nmap'   && ['nmap', 'whois', 'dig', 'curl'].map(t => <span key={t} className="text-xs font-mono text-sovereign-cyan">{t}</span>)}
            {scanType === 'web'    && ['nikto', 'whatweb', 'wafw00f', 'curl'].map(t => <span key={t} className="text-xs font-mono text-sovereign-cyan">{t}</span>)}
            {scanType === 'full'   && Object.keys(tools).map(t => <span key={t} className="text-xs font-mono text-sovereign-cyan">{t}</span>)}
          </div>
        </div>

        <button
          onClick={startScan}
          disabled={scanning || !target.trim()}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-sovereign-cyan text-sovereign-dark font-bold text-sm hover:bg-sovereign-cyan/90 transition-colors disabled:opacity-50"
        >
          {scanning ? (
            <>
              <div className="w-4 h-4 border-2 border-sovereign-dark border-t-transparent rounded-full animate-spin" />
              جارٍ الفحص... (قد يستغرق دقائق)
            </>
          ) : (
            <><Play size={16} /> بدء الفحص</>
          )}
        </button>

        {scanning && (
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
            <div className="w-2 h-2 rounded-full bg-sovereign-cyan animate-pulse" />
            يتم تشغيل الأدوات في الخلفية — سيتحدث التقرير تلقائياً عند الانتهاء
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl mb-5 overflow-hidden">
          {/* Result Header */}
          <div className="flex items-center justify-between p-5 border-b border-sovereign-border">
            <div className="flex items-center gap-4">
              <h3 className="text-sm font-semibold text-white">نتائج الفحص</h3>
              <div className="flex gap-2">
                {criticalCount > 0 && <span className="badge-critical">{criticalCount} حرجة</span>}
                {highCount > 0 && <span className="badge-high">{highCount} عالية</span>}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-sm font-bold ${
                result.risk_level === 'critical' ? 'text-red-400' :
                result.risk_level === 'high' ? 'text-orange-400' :
                result.risk_level === 'medium' ? 'text-yellow-400' : 'text-sovereign-green'
              }`}>
                مستوى المخاطر: {result.risk_level?.toUpperCase()}
              </span>
              <CheckCircle size={16} className="text-sovereign-green" />
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-sovereign-border">
            {[['findings', `النتائج (${findings.length})`], ['ports', 'المنافذ'], ['tech', 'التقنيات'], ['raw', 'Raw Output']].map(([tab, label]) => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 ${activeTab === tab ? 'border-sovereign-cyan text-sovereign-cyan' : 'border-transparent text-slate-400 hover:text-white'}`}>
                {label}
              </button>
            ))}
          </div>

          <div className="p-5">
            {/* Findings Tab */}
            {activeTab === 'findings' && (
              <div className="space-y-2">
                {findings.length === 0 ? (
                  <div className="text-center py-10 text-sovereign-green">
                    <CheckCircle size={36} className="mx-auto mb-2" />
                    <p>لم يتم اكتشاف ثغرات</p>
                  </div>
                ) : findings.map((f, i) => (
                  <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${
                    f.severity === 'critical' ? 'bg-red-900/10 border-red-900/30' :
                    f.severity === 'high'     ? 'bg-orange-900/10 border-orange-900/30' :
                    f.severity === 'medium'   ? 'bg-yellow-900/10 border-yellow-900/30' :
                    'bg-sovereign-dark/30 border-sovereign-border/30'
                  }`}>
                    <span className="text-lg flex-shrink-0 mt-0.5">{SEV_ICON[f.severity] || '⚪'}</span>
                    <div className="flex-1">
                      <div className="text-sm text-white">{f.message}</div>
                      {f.header && <div className="text-xs font-mono text-slate-500 mt-0.5" dir="ltr">{f.header}</div>}
                      {f.port && <div className="text-xs text-slate-500 mt-0.5">المنفذ: {f.port}</div>}
                      <div className="text-[10px] text-slate-600 mt-1">{f.type}</div>
                    </div>
                    <span className={`badge-${f.severity} flex-shrink-0`}>{f.severity}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Ports Tab */}
            {activeTab === 'ports' && (
              <div>
                {result.raw_output?.tools?.nmap?.ports?.length > 0 ? (
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-sovereign-border">
                        {['المنفذ', 'الخدمة', 'الإصدار'].map(h => (
                          <th key={h} className="text-right text-xs text-slate-500 px-3 py-2">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.raw_output.tools.nmap.ports.map((p, i) => (
                        <tr key={i} className="border-b border-sovereign-border/30">
                          <td className="px-3 py-2"><span className="font-mono text-sovereign-cyan text-sm">{p.port}</span></td>
                          <td className="px-3 py-2"><span className="text-sm text-white">{p.service}</span></td>
                          <td className="px-3 py-2"><span className="text-xs text-slate-400 font-mono">{p.version}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-10 text-slate-500 text-sm">
                    {scanType === 'web' ? 'نوع الفحص "web" لا يتضمن فحص المنافذ — استخدم nmap أو full' : 'لا توجد منافذ مفتوحة'}
                  </div>
                )}
              </div>
            )}

            {/* Tech Tab */}
            {activeTab === 'tech' && (
              <div className="space-y-3">
                {result.raw_output?.tools?.whatweb?.length > 0 ? (
                  result.raw_output.tools.whatweb.map((t, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-sovereign-dark/30 border border-sovereign-border/30">
                      <Globe size={16} className="text-sovereign-cyan" />
                      <span className="text-sm text-white font-medium">{t.name}</span>
                      <span className="text-xs font-mono text-slate-400 mr-auto">{t.version}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-10 text-slate-500 text-sm">لا توجد تقنيات مكتشفة</div>
                )}
                {result.raw_output?.tools?.wafw00f && (
                  <div className={`p-3 rounded-lg border ${result.raw_output.tools.wafw00f.has_waf ? 'border-sovereign-green/30 bg-sovereign-green/5' : 'border-yellow-800/30 bg-yellow-900/5'}`}>
                    <div className="flex items-center gap-2">
                      <Shield size={16} className={result.raw_output.tools.wafw00f.has_waf ? 'text-sovereign-green' : 'text-yellow-400'} />
                      <span className="text-sm text-white">
                        {result.raw_output.tools.wafw00f.has_waf
                          ? `WAF مكتشف: ${result.raw_output.tools.wafw00f.name || 'غير محدد'}`
                          : 'لا يوجد WAF'}
                      </span>
                    </div>
                  </div>
                )}
                {result.raw_output?.ssl && (
                  <div className="p-3 rounded-lg border border-sovereign-border/50 bg-sovereign-dark/30">
                    <div className="text-xs text-slate-400 mb-2">معلومات SSL/TLS</div>
                    <div className="space-y-1 text-xs text-slate-300">
                      <div>الحالة: {result.raw_output.ssl.has_ssl ? <span className="text-sovereign-green">✓ مفعّل</span> : <span className="text-red-400">✗ غير مفعّل</span>}</div>
                      {result.raw_output.ssl.issuer && <div>الجهة المصدرة: {result.raw_output.ssl.issuer}</div>}
                      {result.raw_output.ssl.expiry && <div dir="ltr">تاريخ الانتهاء: {result.raw_output.ssl.expiry}</div>}
                    </div>
                  </div>
                )}
                {result.raw_output?.dns?.records && Object.keys(result.raw_output.dns.records).length > 0 && (
                  <div className="p-3 rounded-lg border border-sovereign-border/50 bg-sovereign-dark/30">
                    <div className="text-xs text-slate-400 mb-2">سجلات DNS</div>
                    {Object.entries(result.raw_output.dns.records).map(([type, records]) => (
                      <div key={type} className="mb-1">
                        <span className="text-xs font-mono text-sovereign-cyan">{type}: </span>
                        <span className="text-xs text-slate-300">{Array.isArray(records) ? records.join(', ') : records}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Raw Output Tab */}
            {activeTab === 'raw' && (
              <div className="space-y-4">
                {result.raw_output?.tools && Object.entries(result.raw_output.tools).map(([tool, data]) => (
                  typeof data === 'string' && data.length > 0 && (
                    <div key={tool}>
                      <div className="text-xs font-mono text-sovereign-cyan mb-1"># {tool}</div>
                      <pre className="text-xs text-slate-400 bg-sovereign-dark p-3 rounded-lg overflow-x-auto max-h-48 font-mono" dir="ltr">
                        {data}
                      </pre>
                    </div>
                  )
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* History */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">سجل الفحوصات الأخيرة</h3>
        {history.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">لا توجد فحوصات سابقة</div>
        ) : (
          <div className="space-y-2">
            {history.map(h => (
              <div key={h.id} className="flex items-center justify-between p-3 rounded-lg bg-sovereign-dark/30 border border-sovereign-border/30">
                <div className="flex items-center gap-3">
                  <Clock size={13} className="text-slate-500" />
                  <span className="text-xs font-mono text-slate-400 uppercase">{h.scan_type}</span>
                  {h.risk_level && <span className={`badge-${h.risk_level}`}>{h.risk_level}</span>}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500">{h.started_at ? new Date(h.started_at).toLocaleString('ar-LY') : ''}</span>
                  <span className={`text-xs font-medium ${h.status === 'completed' ? 'text-sovereign-green' : 'text-yellow-400'}`}>
                    {h.status === 'completed' ? '✓ مكتمل' : '⟳ جارٍ'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
