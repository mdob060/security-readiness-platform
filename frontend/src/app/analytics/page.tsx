"use client";

import { PageShell } from "@/components/PageShell";
import { Card, StatCard } from "@/components/Card";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface AnalyticsOverview {
  events_by_source: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  tool_usage: Record<string, number>;
  mean_time_to_resolve_minutes: number | null;
  total_incidents: number;
  total_scan_jobs: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/60",
  high: "bg-orange-500/60",
  medium: "bg-yellow-500/60",
  low: "bg-blue-500/60",
  info: "bg-slate-500/60",
};

function BarList({
  data,
  colorFor,
}: {
  data: Record<string, number>;
  colorFor?: (key: string) => string;
}) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <div className="py-4 text-center text-sm text-slate-500">No data available.</div>;
  }
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div className="flex flex-col gap-3">
      {entries.map(([key, value]) => {
        const pct = Math.max(2, (value / max) * 100);
        const color = colorFor ? colorFor(key) : "bg-blue-500/60";
        return (
          <div key={key}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-slate-400">{key}</span>
              <span className="mono text-slate-300">{value}</span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#1a2029]">
              <div
                className={`h-full rounded-full ${color} transition-all`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsPage() {
  const { data, loading, error } = usePolling(
    () => apiClient.get<AnalyticsOverview>("/api/analytics/overview"),
    [],
    { intervalMs: 20000 }
  );

  const mttr =
    data?.mean_time_to_resolve_minutes === null ||
    data?.mean_time_to_resolve_minutes === undefined
      ? "N/A"
      : `${data.mean_time_to_resolve_minutes.toFixed(1)} min`;

  return (
    <PageShell
      title="Analytics"
      description="Cross-platform operational analytics and reporting metrics"
    >
      <div className="flex flex-col gap-4">
        {error && (
          <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            label="Total Incidents"
            value={loading ? "—" : data?.total_incidents ?? 0}
          />
          <StatCard
            label="Total Scan Jobs"
            value={loading ? "—" : data?.total_scan_jobs ?? 0}
          />
          <StatCard label="Mean Time to Resolve" value={loading ? "—" : mttr} />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card title="Events by Source">
            <BarList data={data?.events_by_source || {}} />
          </Card>
          <Card title="Alerts by Severity">
            <BarList
              data={data?.alerts_by_severity || {}}
              colorFor={(key) => SEVERITY_COLORS[key.toLowerCase()] || "bg-blue-500/60"}
            />
          </Card>
          <Card title="Tool Usage">
            <BarList data={data?.tool_usage || {}} />
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
