import React, { useEffect, useState } from 'react'
import api from '../api/client'
import { BookOpen, ChevronDown, ChevronRight, CheckCircle, AlertCircle } from 'lucide-react'

const CATEGORY_COLORS = {
  incident_response: '#ff4444',
  phishing: '#ff8800',
  availability: '#1a6dff',
  insider_threat: '#9b59b6',
  vulnerability_management: '#ffcc00',
}

const STATIC_PLAYBOOKS = [
  {
    id: 1,
    title: "Ransomware Incident Response Playbook",
    description: "Step-by-step response procedures for ransomware attacks targeting Libyan financial institutions.",
    trigger: "Ransomware detection alert, file extension changes, ransom note discovered",
    category: "incident_response",
    author: "IR Team",
    steps: `1. IMMEDIATE CONTAINMENT (0-15 min):
   - Isolate affected systems from network immediately
   - Disable network shares and mapped drives
   - Block suspicious IPs at firewall level

2. IDENTIFICATION (15-60 min):
   - Identify ransomware family
   - Determine patient zero and infection vector
   - Map extent of encryption across network

3. ERADICATION (1-4 hours):
   - Remove malware from all affected systems
   - Patch exploited vulnerabilities
   - Reset compromised credentials

4. RECOVERY:
   - Restore from clean backups
   - Verify backup integrity before restoration
   - Gradual return to operations with enhanced logging

5. POST-INCIDENT:
   - Document timeline and attack chain
   - Update detection rules
   - Report to CERT-LY`
  },
  {
    id: 2,
    title: "Phishing Email Investigation Playbook",
    description: "Procedures for investigating and responding to phishing campaigns targeting Libyan organizations.",
    trigger: "User reports suspicious email, email gateway alert, credential compromise suspected",
    category: "phishing",
    author: "SOC Team",
    steps: `1. TRIAGE (0-10 min):
   - Collect original email with headers
   - Check if multiple users received same email
   - Assess if any users clicked links or opened attachments

2. ANALYSIS (10-30 min):
   - Analyze email headers for source IP and spoofing
   - Check URLs against threat intel (VirusTotal, URLscan.io)
   - Analyze attachments in sandbox environment

3. CONTAINMENT:
   - Block malicious URLs/domains at proxy/DNS
   - Quarantine similar emails from all mailboxes
   - Force password reset if credentials compromised

4. NOTIFICATION:
   - Notify affected users
   - Alert management if sensitive data at risk
   - Share IOCs with sector peers

5. REMEDIATION:
   - Update email filtering rules
   - Add IOCs to SIEM detection rules
   - Issue security awareness communication`
  },
  {
    id: 3,
    title: "DDoS Attack Mitigation Playbook",
    description: "Response procedures for DDoS attacks against Libyan government and financial sector.",
    trigger: "Network monitoring alert, ISP notification, service unavailability",
    category: "availability",
    author: "Network Security Team",
    steps: `1. DETECTION & CLASSIFICATION (0-5 min):
   - Identify attack type (volumetric, protocol, application layer)
   - Measure attack volume
   - Identify targeted services and IPs

2. IMMEDIATE MITIGATION (5-30 min):
   - Enable upstream DDoS scrubbing
   - Apply rate limiting at edge devices
   - Block attacking IP ranges at border routers

3. TRAFFIC ANALYSIS:
   - Capture attack traffic samples
   - Identify botnet C2 infrastructure
   - Share attack signatures with ISP

4. RECOVERY:
   - Gradually restore filtered traffic
   - Monitor for attack resumption

5. POST-INCIDENT:
   - Report to CERT-LY
   - Review BGP filtering rules
   - Consider CDN/anycast deployment`
  },
  {
    id: 4,
    title: "Insider Threat Detection & Response",
    description: "Playbook for investigating suspected insider threat activity in Libyan organizations.",
    trigger: "UEBA alert, DLP alert, HR notification, anomalous access patterns",
    category: "insider_threat",
    author: "Threat Hunt Team",
    steps: `1. INITIAL ASSESSMENT (Confidential):
   - Brief CISO and HR in confidence
   - Do NOT alert suspect
   - Preserve audit logs immediately (legal hold)

2. COVERT INVESTIGATION:
   - Review DLP logs for data exfiltration attempts
   - Analyze access logs for anomalies
   - Check for unauthorized cloud storage or USB use

3. EVIDENCE PRESERVATION:
   - Forensic image of suspect's device
   - Preserve all relevant logs with chain of custody
   - Coordinate with legal team

4. ESCALATION DECISION:
   - Legal review of findings
   - HR involvement for employment action
   - Law enforcement notification if criminal activity

5. REMEDIATION:
   - Revoke access privileges immediately
   - Conduct access rights audit across organization`
  },
  {
    id: 5,
    title: "Critical Vulnerability Exploitation Response",
    description: "Immediate response when a critical vulnerability is actively exploited in client environments.",
    trigger: "IDS/IPS alert, threat intel notification, vendor emergency advisory",
    category: "vulnerability_management",
    steps: `1. RAPID ASSESSMENT (0-30 min):
   - Identify affected systems in asset inventory
   - Determine exploitation status
   - Assess business impact of affected systems

2. EMERGENCY PATCHING (if available):
   - Test patch in staging environment
   - Deploy emergency patch
   - Verify patch application

3. WORKAROUND (if no patch):
   - Implement compensating controls
   - Restrict network access to vulnerable systems
   - Add virtual patching rule at WAF/IPS

4. HUNT FOR EXPLOITATION:
   - Search logs for exploitation indicators
   - Check for persistence mechanisms
   - Correlate with threat intel

5. TRACKING:
   - Open vulnerability ticket with SLA
   - Track patch deployment status
   - Verify remediation effectiveness`
  }
]

const STATIC_CONTROLS = [
  { control: "SIEM", status: "active", coverage: "85%", alerts_today: 234 },
  { control: "EDR", status: "active", coverage: "92%", detections_today: 12 },
  { control: "WAF", status: "active", coverage: "100%", blocks_today: 1847 },
  { control: "DLP", status: "active", coverage: "78%", violations_today: 3 },
  { control: "NDR", status: "active", coverage: "95%", anomalies_today: 7 },
  { control: "IDS/IPS", status: "active", coverage: "88%", signatures: 45123 },
  { control: "Email Gateway", status: "active", coverage: "100%", blocked_emails_today: 892 },
  { control: "DNS Firewall", status: "active", coverage: "100%", blocked_domains_today: 147 },
  { control: "Threat Intel Platform", status: "active", ioc_count: 23847, feeds: 12 },
  { control: "SOAR", status: "active", automations: 34, tickets_auto_closed_today: 89 },
]

export default function BlueTeam() {
  const [playbooks, setPlaybooks] = useState([])
  const [controls, setControls] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [activeTab, setActiveTab] = useState('playbooks')
  const [usingStatic, setUsingStatic] = useState(false)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [pbRes, ctrlRes] = await Promise.all([
          api.getPlaybooks(),
          api.getDefenseControls()
        ])
        setPlaybooks(pbRes.data)
        setControls(ctrlRes.data)
      } catch (err) {
        // Fallback to static data
        setPlaybooks(STATIC_PLAYBOOKS)
        setControls(STATIC_CONTROLS)
        setUsingStatic(true)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  return (
    <div className="space-y-6 animate-fadeInUp">
      <div>
        <h1 className="text-2xl font-bold text-white">Blue Team</h1>
        <p className="text-sm mt-1" style={{ color: '#6b7fa3' }}>Defensive playbooks and security controls monitoring</p>
      </div>

      {usingStatic && (
        <div className="flex items-center gap-2 p-3 rounded-lg text-xs" style={{ backgroundColor: '#1a6dff11', border: '1px solid #1a6dff22', color: '#6b7fa3' }}>
          <AlertCircle size={12} style={{ color: '#1a6dff' }} />
          Showing sample data. Blue team API endpoints will be available in the updated backend.
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {['playbooks', 'controls'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className="px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all"
            style={{
              backgroundColor: activeTab === tab ? '#00d4ff22' : '#0d1526',
              color: activeTab === tab ? '#00d4ff' : '#6b7fa3',
              border: `1px solid ${activeTab === tab ? '#00d4ff44' : '#1e2d4a'}`
            }}>
            {tab === 'playbooks' ? 'Incident Playbooks' : 'Defense Controls'}
          </button>
        ))}
      </div>

      {activeTab === 'playbooks' && (
        <div className="space-y-3">
          {loading ? (
            [1,2,3].map(i => <div key={i} className="h-20 rounded-xl animate-pulse" style={{ backgroundColor: '#0d1526' }}></div>)
          ) : playbooks.map(pb => (
            <div key={pb.id} className="rounded-xl overflow-hidden" style={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a' }}>
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setExpanded(expanded === pb.id ? null : pb.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg" style={{ backgroundColor: `${CATEGORY_COLORS[pb.category] || '#6b7fa3'}22` }}>
                    <BookOpen size={14} style={{ color: CATEGORY_COLORS[pb.category] || '#6b7fa3' }} />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{pb.title}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs px-1.5 py-0.5 rounded" style={{
                        backgroundColor: `${CATEGORY_COLORS[pb.category] || '#6b7fa3'}22`,
                        color: CATEGORY_COLORS[pb.category] || '#6b7fa3'
                      }}>
                        {pb.category?.replace(/_/g, ' ')}
                      </span>
                      {pb.author && <span className="text-xs" style={{ color: '#6b7fa3' }}>· {pb.author}</span>}
                    </div>
                  </div>
                </div>
                {expanded === pb.id
                  ? <ChevronDown size={14} style={{ color: '#6b7fa3' }} />
                  : <ChevronRight size={14} style={{ color: '#6b7fa3' }} />
                }
              </div>
              {expanded === pb.id && (
                <div className="border-t px-4 pb-4 pt-3 space-y-3" style={{ borderColor: '#1e2d4a' }}>
                  {pb.trigger && (
                    <div>
                      <div className="text-xs font-medium mb-1 uppercase tracking-wide" style={{ color: '#6b7fa3' }}>
                        Trigger Conditions
                      </div>
                      <div className="text-sm" style={{ color: '#ffcc00' }}>{pb.trigger}</div>
                    </div>
                  )}
                  {pb.description && (
                    <p className="text-sm leading-relaxed" style={{ color: '#c8d8e8' }}>{pb.description}</p>
                  )}
                  {pb.steps && (
                    <div>
                      <div className="text-xs font-medium mb-2 uppercase tracking-wide" style={{ color: '#6b7fa3' }}>
                        Response Steps
                      </div>
                      <pre className="text-xs rounded-lg p-4 whitespace-pre-wrap leading-relaxed"
                        style={{ backgroundColor: '#0a0f1e', color: '#c8d8e8', border: '1px solid #1e2d4a', fontFamily: 'inherit' }}>
                        {pb.steps}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'controls' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {loading ? (
            [1,2,3,4].map(i => <div key={i} className="h-24 rounded-xl animate-pulse" style={{ backgroundColor: '#0d1526' }}></div>)
          ) : controls.map(ctrl => (
            <div key={ctrl.control} className="rounded-xl p-4" style={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a' }}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-green-400" />
                  <span className="text-sm font-semibold text-white">{ctrl.control}</span>
                </div>
                <span className="text-xs px-2 py-0.5 rounded bg-green-900/20 text-green-400">{ctrl.status}</span>
              </div>
              <div className="space-y-1.5">
                {ctrl.coverage && (
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: '#6b7fa3' }}>Coverage</span>
                      <span style={{ color: '#00d4ff' }}>{ctrl.coverage}</span>
                    </div>
                    <div className="w-full rounded-full h-1" style={{ backgroundColor: '#1e2d4a' }}>
                      <div className="h-1 rounded-full" style={{ width: ctrl.coverage, backgroundColor: '#00d4ff' }}></div>
                    </div>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-1 mt-2">
                  {ctrl.alerts_today !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Alerts: </span>
                      <span className="font-mono text-orange-400">{ctrl.alerts_today.toLocaleString()}</span>
                    </div>
                  )}
                  {ctrl.blocks_today !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Blocked: </span>
                      <span className="font-mono text-red-400">{ctrl.blocks_today.toLocaleString()}</span>
                    </div>
                  )}
                  {ctrl.detections_today !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Detections: </span>
                      <span className="font-mono text-yellow-400">{ctrl.detections_today}</span>
                    </div>
                  )}
                  {ctrl.ioc_count !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>IOCs: </span>
                      <span className="font-mono" style={{ color: '#00d4ff' }}>{ctrl.ioc_count.toLocaleString()}</span>
                    </div>
                  )}
                  {ctrl.automations !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Automations: </span>
                      <span className="font-mono" style={{ color: '#00d4ff' }}>{ctrl.automations}</span>
                    </div>
                  )}
                  {ctrl.signatures !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Signatures: </span>
                      <span className="font-mono" style={{ color: '#00d4ff' }}>{ctrl.signatures.toLocaleString()}</span>
                    </div>
                  )}
                  {ctrl.blocked_emails_today !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Blocked Emails: </span>
                      <span className="font-mono text-red-400">{ctrl.blocked_emails_today}</span>
                    </div>
                  )}
                  {ctrl.feeds !== undefined && (
                    <div className="text-xs">
                      <span style={{ color: '#6b7fa3' }}>Feeds: </span>
                      <span className="font-mono" style={{ color: '#00d4ff' }}>{ctrl.feeds}</span>
                    </div>
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
