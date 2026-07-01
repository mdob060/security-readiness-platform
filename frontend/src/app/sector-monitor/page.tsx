"use client";

import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { CircularGauge } from "@/components/Gauge";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface SectorStatus {
  sector: string;
  open_alerts: number;
  compliance_score: number;
  updated_at: string;
}

function formatSectorName(sector: string): string {
  return sector
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function SectorMonitorPage() {
  const {
    data: statuses,
    loading,
    error,
  } = usePolling<SectorStatus[]>(
    () => apiClient.get<SectorStatus[]>("/api/sector-monitor/status"),
    []
  );

  return (
    <PageShell
      title="Sector Monitor"
      description="Cross-sector compliance and alert rollup"
    >
      {loading && (
        <div className="py-12 text-center text-slate-500">Loading...</div>
      )}
      {!loading && error && (
        <div className="py-12 text-center text-red-400">{error}</div>
      )}
      {!loading && !error && (statuses ?? []).length === 0 && (
        <div className="py-12 text-center text-slate-500">
          No sector data available.
        </div>
      )}
      {!loading && !error && (statuses ?? []).length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(statuses ?? []).map((s) => (
            <Card key={s.sector} title={formatSectorName(s.sector)}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    Open Alerts
                  </div>
                  <div
                    className={`mt-2 text-3xl font-bold ${
                      s.open_alerts > 0 ? "text-red-400" : "text-slate-100"
                    }`}
                  >
                    {s.open_alerts}
                  </div>
                </div>
                <CircularGauge value={s.compliance_score} label="Compliance" />
              </div>
              <div className="mt-4 mono text-xs text-slate-500">
                Updated: {new Date(s.updated_at).toLocaleString()}
              </div>
            </Card>
          ))}
        </div>
      )}
    </PageShell>
  );
}
