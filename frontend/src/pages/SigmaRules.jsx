import { useEffect, useState } from 'react'
import api from '../api/client'
import { Filter, ToggleLeft, ToggleRight } from 'lucide-react'

const LEVEL_COLORS = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
}

export default function SigmaRules() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.get('/sigma-rules/').then(r => { setRules(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const toggle = (id) => {
    api.patch(`/sigma-rules/${id}/toggle`).then(r => {
      setRules(prev => prev.map(rule => rule.id === id ? { ...rule, is_active: r.data.is_active } : rule))
    })
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">قواعد Sigma</h1>
        <p className="text-slate-400 text-sm mt-1">{rules.filter(r => r.is_active).length} قاعدة مفعّلة من أصل {rules.length}</p>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Rules List */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl overflow-hidden">
          {loading ? (
            <div className="text-center py-10 text-slate-500">جارٍ التحميل...</div>
          ) : (
            <div>
              {rules.map(rule => (
                <div
                  key={rule.id}
                  onClick={() => setSelected(rule)}
                  className={`p-4 border-b border-sovereign-border/50 cursor-pointer transition-colors ${selected?.id === rule.id ? 'bg-sovereign-border/40' : 'hover:bg-sovereign-border/20'}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={LEVEL_COLORS[rule.level]}>{rule.level}</span>
                      <span className="text-xs text-slate-500">{rule.category}</span>
                    </div>
                    <button
                      onClick={e => { e.stopPropagation(); toggle(rule.id) }}
                      className={rule.is_active ? 'text-sovereign-green' : 'text-slate-600'}
                    >
                      {rule.is_active ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
                    </button>
                  </div>
                  <div className="text-sm text-white font-medium">{rule.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5 truncate">{rule.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Rule Detail */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          {selected ? (
            <>
              <div className="flex items-center gap-2 mb-4">
                <span className={LEVEL_COLORS[selected.level]}>{selected.level}</span>
                <h3 className="text-white font-semibold">{selected.title}</h3>
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-xs text-slate-500 mb-1">الوصف</div>
                  <div className="text-slate-300">{selected.description}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">الفئة</div>
                  <div className="text-slate-300">{selected.category}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">الوسوم (MITRE ATT&CK)</div>
                  <div className="flex flex-wrap gap-1">
                    {(selected.tags || '').split(',').map((tag, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-400 border border-blue-800 font-mono">{tag.trim()}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">منطق الكشف</div>
                  <pre className="text-xs bg-sovereign-dark p-3 rounded-lg text-sovereign-cyan font-mono overflow-x-auto" dir="ltr">
                    {selected.detection}
                  </pre>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">المؤلف</div>
                  <div className="text-slate-300">{selected.author}</div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <Filter size={40} className="mb-3 opacity-30" />
              <p className="text-sm">اختر قاعدة لعرض تفاصيلها</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
