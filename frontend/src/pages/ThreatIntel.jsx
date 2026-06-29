import { useEffect, useState } from 'react'
import api from '../api/client'
import { Database, Search, AlertTriangle, CheckCircle } from 'lucide-react'

const TYPE_COLORS = {
  ip: 'text-red-400 bg-red-900/20 border-red-800',
  domain: 'text-orange-400 bg-orange-900/20 border-orange-800',
  hash: 'text-purple-400 bg-purple-900/20 border-purple-800',
  cidr: 'text-yellow-400 bg-yellow-900/20 border-yellow-800',
}

export default function ThreatIntel() {
  const [iocs, setIocs] = useState([])
  const [checkValue, setCheckValue] = useState('')
  const [checkResult, setCheckResult] = useState(null)
  const [checking, setChecking] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/threat-intel/indicators').then(r => { setIocs(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const checkIndicator = () => {
    if (!checkValue.trim()) return
    setChecking(true)
    setCheckResult(null)
    api.post('/threat-intel/check', { indicator: checkValue }).then(r => {
      setCheckResult(r.data)
      setChecking(false)
    }).catch(() => setChecking(false))
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">استخبارات التهديدات</h1>
        <p className="text-slate-400 text-sm mt-1">مؤشرات الاختراق (IOC) والتهديدات المعروفة</p>
      </div>

      {/* IOC Checker */}
      <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5 mb-5">
        <h3 className="text-sm font-semibold text-white mb-3">فحص مؤشر التهديد</h3>
        <div className="flex gap-3">
          <input
            className="flex-1 bg-sovereign-blue border border-sovereign-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovereign-cyan/50 font-mono"
            placeholder="أدخل IP أو نطاق أو Hash..."
            value={checkValue}
            onChange={e => setCheckValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && checkIndicator()}
            dir="ltr"
          />
          <button
            onClick={checkIndicator}
            disabled={checking}
            className="px-5 py-2.5 rounded-lg bg-sovereign-cyan text-sovereign-dark font-semibold text-sm hover:bg-sovereign-cyan/90 transition-colors disabled:opacity-50"
          >
            {checking ? 'جارٍ الفحص...' : 'فحص'}
          </button>
        </div>

        {checkResult && (
          <div className={`mt-4 p-4 rounded-lg border ${checkResult.found ? 'border-red-800 bg-red-900/20' : 'border-green-800 bg-green-900/20'}`}>
            <div className="flex items-center gap-2 mb-2">
              {checkResult.found ? (
                <AlertTriangle size={16} className="text-red-400" />
              ) : (
                <CheckCircle size={16} className="text-green-400" />
              )}
              <span className={`font-semibold ${checkResult.found ? 'text-red-400' : 'text-green-400'}`}>
                {checkResult.found ? 'تهديد مكتشف!' : 'آمن - غير موجود في قاعدة البيانات'}
              </span>
            </div>
            {checkResult.found && (
              <div className="text-sm text-slate-300 space-y-1">
                <div>نوع التهديد: <span className="text-red-300">{checkResult.threat_type}</span></div>
                <div>مستوى الثقة: <span className="text-yellow-300">{checkResult.confidence}%</span></div>
                <div>المصدر: <span className="text-slate-400">{checkResult.source}</span></div>
                <div>{checkResult.description}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* IOC List */}
      {loading ? (
        <div className="text-center py-20 text-slate-500">جارٍ التحميل...</div>
      ) : (
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sovereign-border">
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">المؤشر</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">النوع</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">التهديد</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الثقة</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">المصدر</th>
                <th className="text-right text-xs text-slate-500 font-medium px-4 py-3">الوصف</th>
              </tr>
            </thead>
            <tbody>
              {iocs.map(ioc => (
                <tr key={ioc.id} className="border-b border-sovereign-border/50 hover:bg-sovereign-border/20">
                  <td className="px-4 py-3">
                    <span className="text-xs font-mono text-sovereign-cyan" dir="ltr">{ioc.indicator}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs border ${TYPE_COLORS[ioc.indicator_type] || 'text-slate-400 bg-slate-800 border-slate-700'}`}>
                      {ioc.indicator_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-white">{ioc.threat_type}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-sovereign-border rounded-full overflow-hidden">
                        <div className="h-full bg-sovereign-cyan rounded-full" style={{ width: `${ioc.confidence}%` }} />
                      </div>
                      <span className="text-xs text-slate-400">{ioc.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-slate-400">{ioc.source}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-slate-400">{ioc.description}</span>
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
