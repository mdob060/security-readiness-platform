import { useEffect, useState } from 'react'
import api from '../api/client'
import { AlertTriangle, Filter, Plus } from 'lucide-react'

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/incidents/').then(r => { setIncidents(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const updateStatus = (id, status) => {
    api.patch(`/incidents/${id}`, { status }).then(() => {
      setIncidents(prev => prev.map(i => i.id === id ? { ...i, status } : i))
    })
  }

  const filtered = filter === 'all' ? incidents : incidents.filter(i => i.status === filter)

  const counts = {
    all: incidents.length,
    open: incidents.filter(i => i.status === 'open').length,
    investigating: incidents.filter(i => i.status === 'investigating').length,
    resolved: incidents.filter(i => i.status === 'resolved').length,
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">الحوادث الأمنية</h1>
          <p className="text-slate-400 text-sm mt-1">إدارة ومتابعة جميع الحوادث</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white font-semibold text-sm hover:bg-red-500 transition-colors">
          <Plus size={16} />
          حادثة جديدة
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-5">
        {[['all', 'الكل'], ['open', 'مفتوحة'], ['investigating', 'قيد التحقيق'], ['resolved', 'محلولة']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setFilter(val)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === val
                ? 'bg-sovereign-cyan text-sovereign-dark'
                : 'bg-sovereign-panel border border-sovereign-border text-slate-400 hover:border-sovereign-cyan/30'
            }`}
          >
            {label} ({counts[val]})
          </button>
        ))}
      </div>

      {/* Incidents List */}
      {loading ? (
        <div className="text-center py-20 text-slate-500">جارٍ التحميل...</div>
      ) : (
        <div className="space-y-3">
          {filtered.map(inc => (
            <div key={inc.id} className="bg-sovereign-panel border border-sovereign-border rounded-xl p-4 hover:border-sovereign-cyan/20 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`badge-${inc.severity}`}>{inc.severity}</span>
                    <span className={`badge-${inc.status}`}>{inc.status}</span>
                    {inc.incident_type && (
                      <span className="text-xs px-2 py-0.5 rounded bg-sovereign-border text-slate-400">{inc.incident_type}</span>
                    )}
                  </div>
                  <h3 className="text-white font-semibold">{inc.title}</h3>
                  <p className="text-slate-400 text-sm mt-1">{inc.description}</p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                    <span>العميل: <span className="text-slate-300">{inc.tenant_name}</span></span>
                    <span>المسؤول: <span className="text-slate-300">{inc.assigned_to}</span></span>
                    <span>{new Date(inc.created_at).toLocaleDateString('ar-LY')}</span>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  {inc.status !== 'resolved' && (
                    <button
                      onClick={() => updateStatus(inc.id, inc.status === 'open' ? 'investigating' : 'resolved')}
                      className="text-xs px-3 py-1.5 rounded-lg bg-sovereign-blue border border-sovereign-cyan/30 text-sovereign-cyan hover:bg-sovereign-cyan/10 transition-colors"
                    >
                      {inc.status === 'open' ? 'بدء التحقيق' : 'إغلاق الحادثة'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
