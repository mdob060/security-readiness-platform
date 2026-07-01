"use client";

import { PageShell } from "@/components/PageShell";
import { StatCard, Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface DashboardSummary {
  total_events_24h: number;
  open_alerts: number;
  critical_alerts: number;
  open_incidents: number;
  honeypot_hits: number;
}

interface PipelineItem {
  id: number;
  event_id: number | null;
  alert_id: number | null;
  decision_id: number | null;
  incident_id: number | null;
  stage: string;
  created_at: string;
}

interface Alert {
  id: number;
  title: string;
  severity: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const {
    data: summary,
    loading: summaryLoading,
    error: summaryError,
  } = usePolling(
    () => apiClient.get<DashboardSummary>("/api/dashboard/summary"),
    []
  );
  const { data: pipeline } = usePolling(
    () => apiClient.get<PipelineItem[]>("/api/pipeline/recent"),
    []
  );
  const { data: alerts } = usePolling(
    () => apiClient.get<Alert[]>("/api/soc/alerts?status_filter=open"),
    []
  );

  return (
    <PageShell
      title="Dashboard"
      description="Real-time overview of security posture across the organization"
    >
      {summaryError && (
        <div className="mb-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
          Dashboard summary is unavailable: {summaryError}
        </div>
      )}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        <StatCard
          label="Events (24h)"
          value={summaryLoading ? "…" : summary?.total_events_24h ?? 0}
        />
        <StatCard
          label="Open Alerts"
          value={summaryLoading ? "…" : summary?.open_alerts ?? 0}
          accent="high"
        />
        <StatCard
          label="Critical Alerts"
          value={summaryLoading ? "…" : summary?.critical_alerts ?? 0}
          accent="critical"
        />
        <StatCard
          label="Open Incidents"
          value={summaryLoading ? "…" : summary?.open_incidents ?? 0}
          accent="medium"
        />
        <StatCard
          label="Honeypot Hits"
          value={summaryLoading ? "…" : summary?.honeypot_hits ?? 0}
          accent="low"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Live Pipeline — Recent Activity">
          <div className="flex flex-col gap-2 max-h-96 overflow-y-auto scrollbar-thin">
            {!pipeline || pipeline.length === 0 ? (
              <div className="py-6 text-center text-sm text-slate-500">
                No pipeline activity yet.
              </div>
            ) : (
              pipeline.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between rounded-md border border-[#1e2530] px-3 py-2 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant={p.stage}>{p.stage}</Badge>
                    <span className="mono text-slate-500">
                      {p.event_id ? `evt#${p.event_id}` : ""}
                      {p.alert_id ? ` → alert#${p.alert_id}` : ""}
                      {p.decision_id ? ` → decision#${p.decision_id}` : ""}
                      {p.incident_id ? ` → incident#${p.incident_id}` : ""}
                    </span>
                  </div>
                  <span className="mono text-slate-600">
                    {new Date(p.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card title="Open Alerts — Recent Activity">
          <div className="flex flex-col gap-2 max-h-96 overflow-y-auto scrollbar-thin">
            {!alerts || alerts.length === 0 ? (
              <div className="py-6 text-center text-sm text-slate-500">
                No open alerts.
              </div>
            ) : (
              alerts.slice(0, 20).map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between rounded-md border border-[#1e2530] px-3 py-2 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant={a.severity}>{a.severity}</Badge>
                    <span className="text-slate-300">{a.title}</span>
                  </div>
                  <span className="mono text-slate-600">
                    {new Date(a.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
