import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'cyan',
  trend,
  trendValue,
  loading = false
}) {
  const colorMap = {
    cyan: { text: '#00d4ff', bg: 'rgba(0,212,255,0.08)', border: 'rgba(0,212,255,0.2)' },
    red: { text: '#ff4444', bg: 'rgba(255,68,68,0.08)', border: 'rgba(255,68,68,0.2)' },
    orange: { text: '#ff8800', bg: 'rgba(255,136,0,0.08)', border: 'rgba(255,136,0,0.2)' },
    green: { text: '#00ff88', bg: 'rgba(0,255,136,0.08)', border: 'rgba(0,255,136,0.2)' },
    blue: { text: '#1a6dff', bg: 'rgba(26,109,255,0.08)', border: 'rgba(26,109,255,0.2)' },
    yellow: { text: '#ffcc00', bg: 'rgba(255,204,0,0.08)', border: 'rgba(255,204,0,0.2)' },
  }

  const c = colorMap[color] || colorMap.cyan

  if (loading) {
    return (
      <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a' }}>
        <div className="h-4 bg-slate-700 rounded w-24 mb-3"></div>
        <div className="h-8 bg-slate-700 rounded w-16 mb-2"></div>
        <div className="h-3 bg-slate-700 rounded w-32"></div>
      </div>
    )
  }

  return (
    <div
      className="rounded-xl p-5 transition-all duration-200 hover:scale-[1.02] cursor-default"
      style={{
        backgroundColor: '#0d1526',
        border: `1px solid ${c.border}`,
        boxShadow: `0 0 20px ${c.bg}`,
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="text-sm font-medium" style={{ color: '#6b7fa3' }}>{title}</div>
        {Icon && (
          <div className="p-2 rounded-lg" style={{ backgroundColor: c.bg }}>
            <Icon size={16} style={{ color: c.text }} />
          </div>
        )}
      </div>

      <div className="text-3xl font-bold mb-1" style={{ color: c.text, fontFamily: 'JetBrains Mono, monospace' }}>
        {value !== undefined && value !== null ? value.toLocaleString() : '—'}
      </div>

      <div className="flex items-center gap-2">
        {subtitle && (
          <span className="text-xs" style={{ color: '#6b7fa3' }}>{subtitle}</span>
        )}
        {trend && trendValue && (
          <div className={`flex items-center gap-0.5 text-xs ${trend === 'up' ? 'text-red-400' : 'text-green-400'}`}>
            {trend === 'up' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  )
}
