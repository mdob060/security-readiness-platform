import React, { useEffect, useState } from 'react'
import api from '../api/client'
import { Swords, Target, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'

const PHASE_COLORS = {
  reconnaissance: '#1a6dff',
  initial_access: '#ff8800',
  delivery: '#9b59b6',
  execution: '#ff4444',
  post_exploitation: '#00d4ff',
}

const STATUS_COLORS = {
  planned: '#6b7fa3',
  in_progress: '#ff8800',
  completed: '#00ff88',
}

// Static fallback data for when API doesn't have red team endpoints
const STATIC_OPS = [
  {
    id: 1,
    title: "External Attack Surface Assessment - CBL",
    description: "Full external attack surface assessment of Central Bank of Libya infrastructure. Includes OSINT, port scanning, web application testing, and phishing simulation.",
    phase: "reconnaissance",
    status: "completed",
    operator: "Red Team Lead",
    ttps: "T1595,T1590,T1589,T1598,T1566",
    created_at: "2026-06-10T10:00:00"
  },
  {
    id: 2,
    title: "Adversary Simulation - APT34 TTP Emulation",
    description: "Emulation of APT34 tactics targeting Libyan government infrastructure. Tests defensive controls against known Iranian threat actor TTPs.",
    phase: "execution",
    status: "in_progress",
    operator: "Senior Red Teamer",
    ttps: "T1566.001,T1059.001,T1055,T1071.001,T1041",
    created_at: "2026-06-15T09:00:00"
  },
  {
    id: 3,
    title: "Physical Security Assessment - NOC Facilities",
    description: "Physical penetration testing of NOC facilities including badge cloning, tailgating, and social engineering attempts.",
    phase: "delivery",
    status: "planned",
    operator: "Physical Security Team",
    ttps: "T1190,T1078,T1110",
    created_at: "2026-06-20T14:00:00"
  },
  {
    id: 4,
    title: "Purple Team Exercise - Ransomware Simulation",
    description: "Collaborative purple team exercise simulating a ransomware attack chain from initial access through encryption and lateral movement.",
    phase: "post_exploitation",
    status: "completed",
    operator: "Purple Team",
    ttps: "T1486,T1490,T1489,T1070",
    created_at: "2026-06-01T08:00:00"
  },
  {
    id: 5,
    title: "Social Engineering Campaign - Telecom Staff",
    description: "Targeted vishing and email phishing campaign against telecom sector employees to test security awareness.",
    phase: "initial_access",
    status: "in_progress",
    operator: "Social Engineering Team",
    ttps: "T1566,T1598,T1656",
    created_at: "2026-06-22T11:00:00"
  }
]

const STATIC_TTPS = [
  {"id": "T1566", "name": "Phishing", "tactic": "Initial Access", "subtechniques": ["T1566.001", "T1566.002"]},
  {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
  {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"},
  {"id": "T1055", "name": "Process Injection", "tactic": "Defense Evasion"},
  {"id": "T1003", "name": "OS Credential Dumping", "tactic": "Credential Access"},
  {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
  {"id": "T1486", "name": "Data Encrypted for Impact", "tactic": "Impact"},
  {"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"},
  {"id": "T1071", "name": "Application Layer Protocol", "tactic": "Command and Control"},
  {"id": "T1078", "name": "Valid Accounts", "tactic": "Privilege Escalation"},
  {"id": "T1053", "name": "Scheduled Task/Job", "tactic": "Persistence"},
  {"id": "T1547", "name": "Boot or Logon Autostart Execution", "tactic": "Persistence"},
]

export default function RedTeam() {
  const [ops, setOps] = useState([])
  const [ttps, setTTPs] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [showTTPs, setShowTTPs] = useState(false)
  const [usingStatic, setUsingStatic] = useState(false)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [opsRes, ttpsRes] = await Promise.all([
          api.getRedTeamOps(),
          api.getTTPLibrary()
        ])
        setOps(opsRes.data)
        setTTPs(ttpsRes.data)
      } catch (err) {
        // Fallback to static data if API doesn't have red team endpoints
        setOps(STATIC_OPS)
        setTTPs(STATIC_TTPS)
        setUsingStatic(true)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  const stats = {
    total: ops.length,
    planned: ops.filter(o => o.status === 'planned').length,
    in_progress: ops.filter(o => o.status === 'in_progress').length,
    completed: ops.filter(o => o.status === 'completed').length,
  }

  return (
    <div className="space-y-6 animate-fadeInUp">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Red Team Operations</h1>
          <p className="text-sm mt-1" style={{ color: '#6b7fa3' }}>Adversary simulation and penetration testing operations</p>
        </div>
        <button
          onClick={() => setShowTTPs(!showTTPs)}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
          style={{ backgroundColor: '#ff444422', color: '#ff4444', border: '1px solid #ff444433' }}
        >
          {showTTPs ? 'Hide' : 'View'} MITRE ATT&CK TTPs
        </button>
      </div>

      {usingStatic && (
        <div className="flex items-center gap-2 p-3 rounded-lg text-xs" style={{ backgroundColor: '#1a6dff11', border: '1px solid #1a6dff22', color: '#6b7fa3' }}>
          <AlertCircle size={12} style={{ color: '#1a6dff' }} />
          Showing sample operation data. Red team API endpoints will be available in the updated backend.
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total Ops', value: stats.total, color: '#c8d8e8' },
          { label: 'Planned', value: stats.planned, color: '#6b7fa3' },
          { label: 'In Progress', value: stats.in_progress, color: '#ff8800' },
          { label: 'Completed', value: stats.completed, color: '#00ff88' },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-xl p-4 text-center" style={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a' }}>
            <div className="text-2xl font-bold font-mono" style={{ color }}>{value}</div>
            <div className="text-xs mt-1" style={{ color: '#6b7fa3' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* TTP Library */}
      {showTTPs && (
        <div className="rounded-xl p-5" style={{ backgroundColor: '#0d1526', border: '1px solid #ff444422' }}>
          <h2 className="text-sm font-semibold text-white mb-4">MITRE ATT&CK TTP Library</h2>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {ttps.map(ttp => (
              <div key={ttp.id} className="p-3 rounded-lg" style={{ backgroundColor: '#0a0f1e', border: '1px solid #1e2d4a' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono font-bold" style={{ color: '#ff4444' }}>{ttp.id}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: '#1e2d4a', color: '#6b7fa3' }}>
                    {ttp.tactic}
                  </span>
                </div>
                <div className="text-sm text-white">{ttp.name}</div>
                {ttp.subtechniques && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {ttp.subtechniques.map(sub => (
                      <span key={sub} className="text-xs font-mono" style={{ color: '#6b7fa3' }}>{sub}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Operations List */}
      <div className="space-y-3">
        {loading ? (
          [1,2,3].map(i => <div key={i} className="h-20 rounded-xl animate-pulse" style={{ backgroundColor: '#0d1526' }}></div>)
        ) : ops.map(op => (
          <div key={op.id} className="rounded-xl overflow-hidden" style={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a' }}>
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => setExpanded(expanded === op.id ? null : op.id)}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${PHASE_COLORS[op.phase] || '#6b7fa3'}22` }}>
                  <Swords size={14} style={{ color: PHASE_COLORS[op.phase] || '#6b7fa3' }} />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{op.title}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs px-1.5 py-0.5 rounded" style={{
                      backgroundColor: `${PHASE_COLORS[op.phase] || '#6b7fa3'}22`,
                      color: PHASE_COLORS[op.phase] || '#6b7fa3'
                    }}>
                      {op.phase?.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-medium" style={{ color: STATUS_COLORS[op.status] || '#6b7fa3' }}>
                      {op.status?.replace('_', ' ')}
                    </span>
                    {op.operator && (
                      <span className="text-xs" style={{ color: '#6b7fa3' }}>· {op.operator}</span>
                    )}
                  </div>
                </div>
              </div>
              {expanded === op.id
                ? <ChevronDown size={14} style={{ color: '#6b7fa3' }} />
                : <ChevronRight size={14} style={{ color: '#6b7fa3' }} />
              }
            </div>
            {expanded === op.id && (
              <div className="border-t px-4 pb-4 pt-3" style={{ borderColor: '#1e2d4a' }}>
                {op.description && (
                  <p className="text-sm leading-relaxed mb-3" style={{ color: '#c8d8e8' }}>{op.description}</p>
                )}
                {op.ttps && (
                  <div>
                    <div className="text-xs font-medium mb-2" style={{ color: '#6b7fa3' }}>MITRE ATT&CK TTPs</div>
                    <div className="flex flex-wrap gap-1">
                      {op.ttps.split(',').map(ttp => (
                        <a
                          key={ttp}
                          href={`https://attack.mitre.org/techniques/${ttp.trim().replace('.', '/')}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs px-2 py-0.5 rounded font-mono hover:underline"
                          style={{ backgroundColor: '#ff444422', color: '#ff4444' }}
                        >
                          {ttp.trim()}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
