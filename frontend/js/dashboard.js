/**
 * NATIONAL CYBER DEFENSE PROTOTYPE C+
 * Dashboard Core — Navigation, Clock, Stats
 */

const API = "/api/v1";

// ── Navigation ────────────────────────────────────────────────────────────────
function navigate(pageId) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const page = document.getElementById(`page-${pageId}`);
  if (page) page.classList.add("active");

  const nav = document.querySelector(`[data-page="${pageId}"]`);
  if (nav) nav.classList.add("active");

  // Lazy-load page content
  if (pageId === "overview") loadOverview();
  else if (pageId === "iocs") loadIOCs();
  else if (pageId === "events") loadEvents();
  else if (pageId === "actors") loadActors();
  else if (pageId === "feeds") loadFeeds();
  else if (pageId === "mitre") loadMITRE();
  else if (pageId === "playbooks") loadPlaybooks();
  else if (pageId === "executions") loadExecutions();
  else if (pageId === "lookup") {} // static
}

// ── Clock ─────────────────────────────────────────────────────────────────────
function startClock() {
  function tick() {
    const el = document.getElementById("utc-clock");
    if (el) {
      const now = new Date();
      el.textContent = now.toUTCString().replace(" GMT", " UTC").split(" ").slice(1).join(" ");
    }
  }
  tick();
  setInterval(tick, 1000);
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(message, type = "info", duration = 4000) {
  const icons = { success: "✓", error: "✗", info: "ℹ", warning: "⚠" };
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span style="font-size:15px;">${icons[type] || "•"}</span> <span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(100%)";
    el.style.transition = "0.3s"; setTimeout(() => el.remove(), 300); }, duration);
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(title, bodyHtml, footerHtml = "") {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-body").innerHTML = bodyHtml;
  document.getElementById("modal-footer").innerHTML = footerHtml ||
    `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`;
  document.getElementById("modal-overlay").style.display = "flex";
}

function closeModal() {
  document.getElementById("modal-overlay").style.display = "none";
}

// ── Formatters ────────────────────────────────────────────────────────────────
function severityBadge(s) {
  return `<span class="badge ${s}">${s.toUpperCase()}</span>`;
}

function statusBadge(s) {
  const labels = { active: "ACTIVE", investigating: "INVESTIGATING", mitigated: "MITIGATED",
    resolved: "RESOLVED", false_positive: "FALSE POS.", completed: "COMPLETED",
    failed: "FAILED", running: "RUNNING", idle: "IDLE", paused: "PAUSED" };
  return `<span class="badge ${s}">${labels[s] || s}</span>`;
}

function timeAgo(isoStr) {
  if (!isoStr) return "Never";
  const diff = Date.now() - new Date(isoStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function confidenceBar(conf) {
  const cls = conf >= 80 ? "high" : conf >= 50 ? "medium" : "low";
  return `<div class="confidence-bar">
    <div class="conf-track"><div class="conf-fill ${cls}" style="width:${conf}%"></div></div>
    <span class="conf-value">${conf}%</span>
  </div>`;
}

function tagsHtml(tags) {
  if (!tags || !tags.length) return "";
  return `<div class="tags">${tags.map(t => `<span class="tag">${t}</span>`).join("")}</div>`;
}

// ── API fetch ─────────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API + path, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error("API error:", e);
    toast(`API Error: ${e.message}`, "error");
    return null;
  }
}

// ── Overview ──────────────────────────────────────────────────────────────────
async function loadOverview() {
  const [stats, metrics] = await Promise.all([
    apiFetch("/threats/stats"),
    apiFetch("/response/metrics"),
  ]);

  if (stats) {
    document.getElementById("stat-total-iocs").textContent = stats.total_iocs;
    document.getElementById("stat-critical-iocs").textContent = stats.critical_iocs;
    document.getElementById("stat-active-threats").textContent = stats.active_threats;
    document.getElementById("stat-total-events").textContent = stats.total_events;
    document.getElementById("stat-actors").textContent = stats.threat_actors;
    document.getElementById("stat-feeds").textContent = `${stats.active_feeds}/${stats.total_feeds}`;
  }

  if (metrics) {
    document.getElementById("stat-executions").textContent = metrics.total_executions;
    document.getElementById("stat-blocked").textContent = metrics.threats_blocked;
  }

  // Recent events
  const events = await apiFetch("/threats/events?limit=5");
  if (events) {
    const tbody = document.getElementById("recent-events-body");
    tbody.innerHTML = events.map(e => `
      <tr onclick="showEventDetail('${e.id}')">
        <td class="td-mono">${e.id}</td>
        <td>${e.title}</td>
        <td>${severityBadge(e.severity)}</td>
        <td>${statusBadge(e.status)}</td>
        <td style="color:var(--text-muted);font-size:12px;">${timeAgo(e.timestamp)}</td>
      </tr>`).join("");
  }
}

// ── IOC Lookup (standalone) ───────────────────────────────────────────────────
async function lookupIOC() {
  const val = document.getElementById("lookup-input").value.trim();
  if (!val) { toast("Enter a value to look up", "warning"); return; }

  const result = await apiFetch(`/threats/iocs/search/lookup?value=${encodeURIComponent(val)}`);
  const out = document.getElementById("lookup-result");
  out.classList.add("show");

  if (!result) return;

  if (result.found && result.ioc) {
    const ioc = result.ioc;
    out.innerHTML = `<div class="hit">
⚠  IOC MATCH FOUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Value      : ${ioc.value}
Type       : ${ioc.type.toUpperCase()}
Severity   : ${ioc.severity.toUpperCase()}
Confidence : ${ioc.confidence}%
Source     : ${ioc.source}
First Seen : ${new Date(ioc.first_seen).toLocaleString()}
Last Seen  : ${new Date(ioc.last_seen).toLocaleString()}
Hit Count  : ${ioc.hit_count}
MITRE TTPs : ${ioc.mitre_techniques.join(", ") || "N/A"}
Tags       : ${ioc.tags.join(", ") || "None"}

Description: ${ioc.description}
</div>`;
  } else {
    out.innerHTML = `<span class="clean">✓  CLEAN — "${val}" not found in threat intelligence database.</span>`;
  }
}

// ── Event Detail Modal ────────────────────────────────────────────────────────
async function showEventDetail(eventId) {
  const e = await apiFetch(`/threats/events/${eventId}`);
  if (!e) return;

  const body = `
    <div class="info-row"><span class="info-label">Title</span><span class="info-value">${e.title}</span></div>
    <div class="info-row"><span class="info-label">Severity</span>${severityBadge(e.severity)}</div>
    <div class="info-row"><span class="info-label">Status</span>${statusBadge(e.status)}</div>
    <div class="info-row"><span class="info-label">Timestamp</span><span class="info-value">${new Date(e.timestamp).toLocaleString()}</span></div>
    <div class="info-row"><span class="info-label">Source IP</span><span class="info-value td-mono">${e.source_ip || "N/A"}</span></div>
    <div class="info-row"><span class="info-label">Destination IP</span><span class="info-value td-mono">${e.destination_ip || "N/A"}</span></div>
    <div class="info-row"><span class="info-label">Threat Actor</span><span class="info-value" style="color:var(--critical)">${e.actor || "Unknown"}</span></div>
    <div class="info-row"><span class="info-label">MITRE TTPs</span><span class="info-value">${e.mitre_techniques.map(t => `<span class="tag">${t}</span>`).join(" ") || "N/A"}</span></div>
    <div class="divider"></div>
    <div style="font-size:13px;color:var(--text-secondary);line-height:1.6">${e.description}</div>
    <div class="divider"></div>
    <div style="font-size:11px;color:var(--text-muted)">Change Status:</div>
    <div style="display:flex;gap:8px;margin-top:8px">
      ${["active","investigating","mitigated","resolved"].map(s =>
        `<button class="btn btn-sm btn-secondary" onclick="changeEventStatus('${e.id}','${s}');closeModal();">${s}</button>`
      ).join("")}
    </div>`;

  openModal(`EVENT — ${e.id}`, body);
}

async function changeEventStatus(eventId, status) {
  await apiFetch(`/threats/events/${eventId}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  toast(`Event ${eventId} status → ${status}`, "success");
  loadEvents();
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  startClock();
  navigate("overview");

  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => navigate(item.dataset.page));
  });

  document.getElementById("modal-overlay").addEventListener("click", e => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Auto-refresh active threats badge every 30s
  setInterval(async () => {
    const stats = await apiFetch("/threats/stats");
    if (stats && stats.active_threats > 0) {
      document.getElementById("nav-badge-events").textContent = stats.active_threats;
    }
  }, 30000);
});
