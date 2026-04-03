/**
 * NATIONAL CYBER DEFENSE PROTOTYPE C+
 * Automated Response Module — Playbooks & Executions
 */

// ── Playbooks ─────────────────────────────────────────────────────────────────
async function loadPlaybooks() {
  const playbooks = await apiFetch("/response/playbooks");
  if (!playbooks) return;

  const container = document.getElementById("playbooks-grid");
  container.innerHTML = playbooks.map(pb => `
    <div class="playbook-card ${pb.enabled ? '' : 'disabled'}" id="pb-${pb.id}">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
        <div>
          <div class="playbook-name">${pb.name}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">
            ${pb.auto_execute
              ? '<span class="auto-badge">⚡ AUTO-EXECUTE</span>'
              : '<span class="manual-badge">👤 MANUAL APPROVAL</span>'}
          </div>
        </div>
        <div class="status-dot ${pb.enabled ? '' : 'red'}"></div>
      </div>

      <div class="playbook-desc">${pb.description}</div>

      <div class="playbook-meta">
        <div class="playbook-meta-item">Runs: <strong>${pb.run_count}</strong></div>
        <div class="playbook-meta-item">Success: <strong>${pb.success_rate}%</strong></div>
        <div class="playbook-meta-item">Severity: <strong>${pb.severity_threshold.toUpperCase()}</strong></div>
        <div class="playbook-meta-item">Last Run: <strong>${timeAgo(pb.last_run)}</strong></div>
      </div>

      <div class="playbook-actions-preview">
        ${pb.actions.slice(0, 5).map(a =>
          `<span class="action-chip">${a.name}</span>`
        ).join("")}
        ${pb.actions.length > 5 ? `<span class="action-chip">+${pb.actions.length - 5} more</span>` : ""}
      </div>

      <div class="playbook-footer">
        <div>${tagsHtml(pb.tags.slice(0, 3))}</div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-sm btn-secondary"
            onclick="togglePlaybook('${pb.id}');event.stopPropagation()">
            ${pb.enabled ? "Disable" : "Enable"}
          </button>
          <button class="btn btn-sm btn-primary"
            onclick="runPlaybook('${pb.id}');event.stopPropagation()">
            ▶ Run
          </button>
        </div>
      </div>
    </div>`).join("");
}

async function togglePlaybook(playbookId) {
  const pb = await apiFetch(`/response/playbooks/${playbookId}/toggle`, { method: "POST" });
  if (pb) {
    toast(`Playbook "${pb.name}" ${pb.enabled ? "enabled" : "disabled"}`, pb.enabled ? "success" : "info");
    loadPlaybooks();
  }
}

async function runPlaybook(playbookId) {
  toast("Executing playbook...", "info");

  const pb = await apiFetch(`/response/playbooks/${playbookId}`);
  if (!pb) return;

  const execution = await apiFetch(`/response/playbooks/${playbookId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ triggered_by: "analyst" }),
  });

  if (!execution) return;

  const success = execution.status === "completed";
  toast(
    `Playbook "${pb.name}" ${success ? "completed successfully" : "failed"}`,
    success ? "success" : "error"
  );

  showExecutionDetail(execution);
  loadPlaybooks();
}

// ── Executions ────────────────────────────────────────────────────────────────
async function loadExecutions() {
  const [executions, metrics] = await Promise.all([
    apiFetch("/response/executions?limit=50"),
    apiFetch("/response/metrics"),
  ]);

  if (metrics) {
    document.getElementById("rsp-total").textContent = metrics.total_executions;
    document.getElementById("rsp-success").textContent = metrics.successful;
    document.getElementById("rsp-failed").textContent = metrics.failed;
    document.getElementById("rsp-blocked").textContent = metrics.threats_blocked;
    document.getElementById("rsp-isolated").textContent = metrics.hosts_isolated;
    document.getElementById("rsp-ips").textContent = metrics.ips_blocked;
    document.getElementById("rsp-avg").textContent = `${metrics.avg_response_time_ms}ms`;
    document.getElementById("rsp-alerts").textContent = metrics.alerts_sent;
  }

  if (!executions) return;

  const container = document.getElementById("executions-list");
  if (!executions.length) {
    container.innerHTML = `<div class="loading">No executions recorded yet. Run a playbook to see results.</div>`;
    return;
  }

  container.innerHTML = executions.map(ex => `
    <div class="exec-row" onclick="showExecutionDetail(null, '${ex.execution_id}')">
      <div class="status-dot ${ex.status === 'completed' ? '' : 'red'}"></div>
      <div style="flex:1">
        <div style="font-size:13px;font-weight:600">${ex.playbook_name}</div>
        <div style="font-size:11px;color:var(--text-muted)">${ex.execution_id} · ${timeAgo(ex.triggered_at)}</div>
      </div>
      ${statusBadge(ex.status)}
      <div style="font-size:12px;color:var(--text-muted);font-family:var(--font-mono)">${ex.total_duration_ms}ms</div>
      <div style="font-size:12px;color:var(--text-secondary)">${ex.triggered_by}</div>
    </div>`).join("");
}

async function showExecutionDetail(execution, executionId) {
  if (!execution && executionId) {
    execution = await apiFetch(`/response/executions/${executionId}`);
    if (!execution) return;
  }

  const body = `
    <div class="info-row"><span class="info-label">Execution ID</span><span class="info-value td-mono">${execution.execution_id}</span></div>
    <div class="info-row"><span class="info-label">Playbook</span><span class="info-value">${execution.playbook_name}</span></div>
    <div class="info-row"><span class="info-label">Status</span>${statusBadge(execution.status)}</div>
    <div class="info-row"><span class="info-label">Triggered By</span><span class="info-value">${execution.triggered_by}</span></div>
    <div class="info-row"><span class="info-label">Started</span><span class="info-value">${new Date(execution.triggered_at).toLocaleString()}</span></div>
    <div class="info-row"><span class="info-label">Completed</span><span class="info-value">${execution.completed_at ? new Date(execution.completed_at).toLocaleString() : "—"}</span></div>
    <div class="info-row"><span class="info-label">Total Duration</span><span class="info-value" style="font-family:var(--font-mono);color:var(--accent-cyan)">${execution.total_duration_ms}ms</span></div>
    ${execution.event_id ? `<div class="info-row"><span class="info-label">Event ID</span><span class="info-value td-mono">${execution.event_id}</span></div>` : ""}
    <div class="divider"></div>
    <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:var(--text-muted);margin-bottom:8px">ACTION RESULTS</div>
    ${execution.actions.map(action => `
      <div class="action-step">
        <div class="step-number ${action.result}">
          ${action.result === "success" ? "✓" : action.result === "failed" ? "✗" : action.step}
        </div>
        <div class="action-detail">
          <div class="action-name">${action.name}</div>
          <div class="action-type-label">${action.action_type.toUpperCase()}</div>
          ${action.output ? `<div class="action-output">${action.output}</div>` : ""}
        </div>
        <div class="action-duration">${action.duration_ms}ms</div>
      </div>`).join("")}`;

  openModal(`EXECUTION — ${execution.execution_id}`, body);
}
