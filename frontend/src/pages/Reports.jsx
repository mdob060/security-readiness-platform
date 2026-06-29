import { useEffect, useState } from 'react'
import api from '../api/client'
import { FileText, Plus, Download } from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [selectedTenant, setSelectedTenant] = useState('')
  const [selectedReport, setSelectedReport] = useState(null)

  useEffect(() => {
    api.get('/reports/').then(r => { setReports(r.data); setLoading(false) }).catch(() => setLoading(false))
    api.get('/tenants/').then(r => setTenants(r.data)).catch(() => {})
  }, [])

  const generateReport = () => {
    if (!selectedTenant) return
    setGenerating(true)
    const tenant = tenants.find(t => t.id === parseInt(selectedTenant))
    api.post('/reports/generate', {
      tenant_id: parseInt(selectedTenant),
      title: `تقرير الجاهزية الأمنية - ${tenant?.name}`,
      report_type: 'engagement_summary',
    }).then(r => {
      setReports(prev => [{ ...r.data, tenant_name: tenant?.name }, ...prev])
      setSelectedReport(r.data)
      setGenerating(false)
    }).catch(() => setGenerating(false))
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">التقارير</h1>
          <p className="text-slate-400 text-sm mt-1">ملخصات التعامل - {tenants.length} عميل</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-4">
          <div className="text-2xl font-bold text-white">{tenants.length}</div>
          <div className="text-xs text-slate-400 mt-1">إجمالي العملاء</div>
          <div className="text-xs text-sovereign-cyan mt-1">TENANTS</div>
        </div>
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-4">
          <div className="text-2xl font-bold text-white">{reports.length}</div>
          <div className="text-xs text-slate-400 mt-1">تقارير صادرة</div>
        </div>
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-4">
          <div className="text-2xl font-bold text-sovereign-green">{reports.filter(r => r.status === 'completed').length}</div>
          <div className="text-xs text-slate-400 mt-1">تقارير مكتملة</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Generate Report */}
        <div className="bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">إنشاء تقرير جديد</h3>
          <select
            className="w-full bg-sovereign-blue border border-sovereign-border rounded-lg px-3 py-2.5 text-sm text-white mb-3 focus:outline-none focus:border-sovereign-cyan/50"
            value={selectedTenant}
            onChange={e => setSelectedTenant(e.target.value)}
          >
            <option value="">اختر العميل...</option>
            {tenants.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <button
            onClick={generateReport}
            disabled={!selectedTenant || generating}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sovereign-cyan text-sovereign-dark font-semibold text-sm hover:bg-sovereign-cyan/90 transition-colors disabled:opacity-50"
          >
            <Plus size={16} />
            {generating ? 'جارٍ الإنشاء...' : 'إنشاء التقرير'}
          </button>

          <div className="mt-5 space-y-2">
            {loading ? (
              <div className="text-center text-slate-500 text-sm py-4">جارٍ التحميل...</div>
            ) : reports.map(r => (
              <button
                key={r.id}
                onClick={() => {
                  api.get(`/reports/${r.id}`).then(res => setSelectedReport(res.data))
                }}
                className="w-full text-right p-3 rounded-lg border border-sovereign-border hover:border-sovereign-cyan/30 transition-colors"
              >
                <div className="text-sm text-white truncate">{r.title}</div>
                <div className="text-xs text-slate-500 mt-0.5">{r.tenant_name} · {new Date(r.created_at).toLocaleDateString('ar-LY')}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Report Viewer */}
        <div className="col-span-2 bg-sovereign-panel border border-sovereign-border rounded-xl p-5">
          {selectedReport ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white">{selectedReport.title}</h3>
                <button className="flex items-center gap-1 text-xs text-sovereign-cyan hover:underline">
                  <Download size={13} />
                  تنزيل PDF
                </button>
              </div>
              <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono bg-sovereign-dark/50 rounded-lg p-4 overflow-y-auto max-h-[500px]" dir="rtl">
                {selectedReport.content}
              </pre>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <FileText size={40} className="mb-3 opacity-30" />
              <p className="text-sm">اختر تقريراً أو أنشئ تقريراً جديداً</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
