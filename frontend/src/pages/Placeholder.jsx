import { useLocation } from 'react-router-dom'
import { Wrench } from 'lucide-react'

export default function Placeholder() {
  const location = useLocation()
  const name = location.pathname.replace('/', '').replace(/-/g, ' ')

  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-slate-500">
      <Wrench size={48} className="mb-4 opacity-30" />
      <h2 className="text-lg font-semibold text-slate-300 mb-2 capitalize">{name || 'الصفحة'}</h2>
      <p className="text-sm">هذا القسم قيد التطوير</p>
      <span className="mt-3 px-3 py-1 rounded-full bg-sovereign-cyan/10 text-sovereign-cyan text-xs border border-sovereign-cyan/30">
        قريباً
      </span>
    </div>
  )
}
