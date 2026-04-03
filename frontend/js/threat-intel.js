/**
 * NATIONAL CYBER DEFENSE PROTOTYPE C+
 * Threat Intelligence Module — IOCs, Events, Actors, Feeds, MITRE
 */

// ── IOCs ──────────────────────────────────────────────────────────────────────
async function loadIOCs(filter = {}) {
  const params = new URLSearchParams();
  if (filter.type) params.set("ioc_type", filter.type);
  if (filter.severity) params.set("severity", filter.severity);
  if (filter.search) params.set("search", filter.search);

  const iocs = await apiFetch(`/threats/iocs?${params.toString()}`);
  if (!iocs) return;

  const tbody = document.getElementById("iocs-tbody");
  tbody.innerHTML = iocs.map(ioc => `
    <tr onclick="showIOCDetail('${ioc.id}')">
      <td><span class="badge info">${ioc.type.toUpperCase()}</span></td>
      <td><span class="ioc-value" title="${ioc.value}">${ioc.value}</span></td>
      <td>${severityBadge(ioc.severity)}</td>
      <td>${confidenceBar(ioc.confidence)}</td>
      <td style="font-size:12px;color:var(--text-secondary)">${ioc.source}</td>
      <td>${tagsHtml(ioc.tags.slice(0, 3))}</td>
      <td style="font-size:12px;color:var(--text-muted)">${timeAgo(ioc.last_seen)}</td>
      <td><span style="font-family:var(--font-mono);color:var(--accent-blue)">${ioc.hit_count}</span></td>
    </tr>`).join("") || `<tr><td colspan="8" class="loading">No IOCs found</td></tr>`;
}

async function showIOCDetail(iocId) {
  const ioc = await apiFetch(`/threats/iocs/${iocId}`);
  if (!ioc) return;

  const body = `
    <div class="info-row"><span class="info-label">Type</span><span class="badge info">${ioc.type.toUpperCase()}</span></div>
    <div class="info-row"><span class="info-label">Value</span><span class="info-value td-mono">${ioc.value}</span></div>
    <div class="info-row"><span class="info-label">Severity</span>${severityBadge(ioc.severity)}</div>
    <div class="info-row"><span class="info-label">Confidence</span>${confidenceBar(ioc.confidence)}</div>
    <div class="info-row"><span class="info-label">Source</span><span class="info-value">${ioc.source}</span></div>
    <div class="info-row"><span class="info-label">First Seen</span><span class="info-value">${new Date(ioc.first_seen).toLocaleString()}</span></div>
    <div class="info-row"><span class="info-label">Last Seen</span><span class="info-value">${new Date(ioc.last_seen).toLocaleString()}</span></div>
    <div class="info-row"><span class="info-label">Hit Count</span><span class="info-value" style="color:var(--accent-blue);font-family:var(--font-mono)">${ioc.hit_count}</span></div>
    <div class="info-row"><span class="info-label">MITRE TTPs</span><span class="info-value">${ioc.mitre_techniques.map(t => `<span class="tag">${t}</span>`).join(" ") || "N/A"}</span></div>
    <div class="info-row"><span class="info-label">Tags</span>${tagsHtml(ioc.tags)}</div>
    <div class="divider"></div>
    <div style="font-size:13px;color:var(--text-secondary);line-height:1.6">${ioc.description || "No description."}</div>`;

  openModal(`IOC — ${ioc.value}`, body, `
    <button class="btn btn-danger btn-sm" onclick="deleteIOC('${ioc.id}')">Delete IOC</button>
    <button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
}

async function deleteIOC(iocId) {
  await apiFetch(`/threats/iocs/${iocId}`, { method: "DELETE" });
  toast("IOC deleted", "success");
  closeModal();
  loadIOCs();
}

function filterIOCs() {
  loadIOCs({
    type: document.getElementById("ioc-type-filter").value,
    severity: document.getElementById("ioc-severity-filter").value,
    search: document.getElementById("ioc-search").value,
  });
}

// ── Events ────────────────────────────────────────────────────────────────────
async function loadEvents(filter = {}) {
  const params = new URLSearchParams();
  if (filter.severity) params.set("severity", filter.severity);
  if (filter.status) params.set("status", filter.status);

  const events = await apiFetch(`/threats/events?${params.toString()}&limit=50`);
  if (!events) return;

  const tbody = document.getElementById("events-tbody");
  tbody.innerHTML = events.map(e => `
    <tr onclick="showEventDetail('${e.id}')">
      <td class="td-mono">${e.id}</td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${e.title}</td>
      <td>${severityBadge(e.severity)}</td>
      <td>${statusBadge(e.status)}</td>
      <td class="td-mono" style="font-size:11px">${e.source_ip || "—"}</td>
      <td style="font-size:12px;color:var(--critical)">${e.actor || "—"}</td>
      <td>${e.mitre_techniques.slice(0,3).map(t => `<span class="tag">${t}</span>`).join(" ")}</td>
      <td style="color:var(--text-muted);font-size:12px">${timeAgo(e.timestamp)}</td>
    </tr>`).join("") || `<tr><td colspan="8" class="loading">No events found</td></tr>`;
}

function filterEvents() {
  loadEvents({
    severity: document.getElementById("evt-severity-filter").value,
    status: document.getElementById("evt-status-filter").value,
  });
}

// ── Threat Actors ─────────────────────────────────────────────────────────────
async function loadActors() {
  const actors = await apiFetch("/threats/actors");
  if (!actors) return;

  const container = document.getElementById("actors-grid");
  container.innerHTML = actors.map(a => `
    <div class="actor-card" onclick="showActorDetail('${a.id}')">
      <div class="actor-header">
        <div>
          <div class="actor-name">${a.name}</div>
          <div class="actor-origin">📍 ${a.origin} · ${a.sophistication}</div>
        </div>
        <div class="status-dot ${a.active ? '' : 'red'}" title="${a.active ? 'Active' : 'Inactive'}"></div>
      </div>
      <div class="actor-motivation">${a.motivation}</div>
      <div class="actor-aliases">
        ${a.aliases.map(alias => `<span class="alias-tag">${alias}</span>`).join("")}
      </div>
      <div style="margin-top:10px">${tagsHtml(a.ttps.slice(0,4))}</div>
    </div>`).join("");
}

async function showActorDetail(actorId) {
  const a = await apiFetch(`/threats/actors/${actorId}`);
  if (!a) return;

  const body = `
    <div class="info-row"><span class="info-label">Name</span><span class="info-value" style="color:var(--critical);font-weight:700">${a.name}</span></div>
    <div class="info-row"><span class="info-label">Aliases</span><span class="info-value">${a.aliases.join(", ")}</span></div>
    <div class="info-row"><span class="info-label">Origin</span><span class="info-value">${a.origin}</span></div>
    <div class="info-row"><span class="info-label">Motivation</span><span class="info-value">${a.motivation}</span></div>
    <div class="info-row"><span class="info-label">Sophistication</span><span class="info-value">${a.sophistication}</span></div>
    <div class="info-row"><span class="info-label">Status</span><span class="info-value">${a.active ? '🔴 Active' : '⚫ Inactive'}</span></div>
    <div class="info-row"><span class="info-label">MITRE Groups</span><span class="info-value">${a.mitre_groups.join(", ") || "N/A"}</span></div>
    <div class="info-row"><span class="info-label">Known TTPs</span>${tagsHtml(a.ttps)}</div>
    <div class="divider"></div>
    <div style="font-size:13px;color:var(--text-secondary);line-height:1.6">${a.description}</div>`;

  openModal(`THREAT ACTOR — ${a.name}`, body);
}

// ── Feeds ─────────────────────────────────────────────────────────────────────
async function loadFeeds() {
  const feeds = await apiFetch("/threats/feeds");
  if (!feeds) return;

  const container = document.getElementById("feeds-list");
  container.innerHTML = feeds.map(f => `
    <div class="feed-item">
      <div class="feed-status ${f.enabled ? 'enabled' : 'disabled'}" title="${f.enabled ? 'Active' : 'Disabled'}"></div>
      <div class="feed-info">
        <div class="feed-name">${f.name}</div>
        <div class="feed-provider">${f.provider} · ${f.feed_type} · Updated ${timeAgo(f.last_updated)}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${f.description}</div>
      </div>
      <div class="feed-count">
        ${f.ioc_count.toLocaleString()}
        <span>IOCs</span>
      </div>
      <button class="btn btn-sm ${f.enabled ? 'btn-secondary' : 'btn-success'}"
        onclick="toggleFeed('${f.id}');event.stopPropagation()">
        ${f.enabled ? 'Disable' : 'Enable'}
      </button>
    </div>`).join("");
}

async function toggleFeed(feedId) {
  const feed = await apiFetch(`/threats/feeds/${feedId}/toggle`, { method: "POST" });
  if (feed) {
    toast(`Feed "${feed.name}" ${feed.enabled ? "enabled" : "disabled"}`, feed.enabled ? "success" : "info");
    loadFeeds();
  }
}

// ── MITRE ATT&CK ──────────────────────────────────────────────────────────────
async function loadMITRE() {
  const techniques = await apiFetch("/threats/mitre/techniques");
  if (!techniques) return;

  const container = document.getElementById("mitre-grid");
  container.innerHTML = techniques.map(t => `
    <div class="mitre-technique-card" onclick="showTechniqueDetail('${t.technique_id}')">
      <div class="mitre-id">${t.technique_id}</div>
      <div class="mitre-name">${t.name}</div>
      <div class="mitre-tactic">${t.tactic}</div>
      <div style="margin-top:6px">${tagsHtml(t.platforms.slice(0,3))}</div>
    </div>`).join("");
}

async function showTechniqueDetail(techniqueId) {
  const t = await apiFetch(`/threats/mitre/techniques/${techniqueId}`);
  if (!t) return;

  const body = `
    <div class="info-row"><span class="info-label">Technique ID</span><span class="info-value td-mono" style="color:var(--accent-cyan)">${t.technique_id}</span></div>
    <div class="info-row"><span class="info-label">Name</span><span class="info-value" style="font-weight:700">${t.name}</span></div>
    <div class="info-row"><span class="info-label">Tactic</span><span class="badge medium">${t.tactic}</span></div>
    <div class="info-row"><span class="info-label">Platforms</span>${tagsHtml(t.platforms)}</div>
    <div class="divider"></div>
    <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;line-height:1.6">${t.description}</div>
    <div style="margin-bottom:10px">
      <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:var(--accent-cyan);margin-bottom:6px">DETECTION</div>
      <div style="font-size:13px;color:var(--text-secondary)">${t.detection}</div>
    </div>
    <div>
      <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:var(--success);margin-bottom:6px">MITIGATION</div>
      <div style="font-size:13px;color:var(--text-secondary)">${t.mitigation}</div>
    </div>`;

  openModal(`MITRE ATT&CK — ${t.technique_id}`, body);
}
