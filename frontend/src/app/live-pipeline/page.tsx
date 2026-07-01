"use client";

import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface PipelineItem {
  id: number;
  event_id: number | null;
  alert_id: number | null;
  decision_id: number | null;
  incident_id: number | null;
  stage: "event" | "alert" | "decision" | "incident" | string;
  created_at: string;
}

const STAGES: { key: PipelineItem["stage"]; label: string }[] = [
  { key: "event", label: "Event" },
  { key: "alert", label: "Alert" },
  { key: "decision", label: "Decision" },
  { key: "incident", label: "Incident" },
];

function stageId(item: PipelineItem, stage: string): number | null {
  switch (stage) {
    case "event":
      return item.event_id;
    case "alert":
      return item.alert_id;
    case "decision":
      return item.decision_id;
    case "incident":
      return item.incident_id;
    default:
      return null;
  }
}

function Chip({
  label,
  id,
  active,
}: {
  label: string;
  id: number | null;
  active: boolean;
}) {
  const reached = id !== null && id !== undefined;
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-1 text-xs font-medium mono ${
        active
          ? "border-blue-500 bg-blue-600/20 text-blue-300"
          : reached
          ? "border-[#1e2530] bg-[#11161d] text-slate-300"
          : "border-dashed border-[#1e2530] text-slate-600"
      }`}
    >
      {label} {reached ? `#${id}` : "—"}
    </span>
  );
}

export default function LivePipelinePage() {
  const {
    data: pipeline,
    loading,
    error,
  } = usePolling(() => apiClient.get<PipelineItem[]>("/api/pipeline/recent"), []);

  const rows = (pipeline ?? [])
    .slice()
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

  return (
    <PageShell
      title="Live Pipeline"
      description="Real-time view of events flowing through the detection and response pipeline (auto-refreshes every 10s)"
    >
      <Card title="Pipeline Activity">
        {loading && rows.length === 0 && (
          <div className="py-6 text-center text-sm text-slate-500">
            Loading pipeline activity...
          </div>
        )}
        {error && (
          <div className="py-6 text-center text-sm text-red-400">{error}</div>
        )}
        {!loading && !error && rows.length === 0 && (
          <div className="py-6 text-center text-sm text-slate-500">
            No pipeline activity yet.
          </div>
        )}
        {rows.length > 0 && (
          <div className="flex flex-col gap-2">
            {rows.map((item) => (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[#1e2530] px-3 py-2"
              >
                <div className="flex items-center gap-1.5">
                  {STAGES.map((s, idx) => (
                    <span key={s.key} className="flex items-center gap-1.5">
                      <Chip
                        label={s.label}
                        id={stageId(item, s.key)}
                        active={item.stage === s.key}
                      />
                      {idx < STAGES.length - 1 && (
                        <span className="text-slate-700">→</span>
                      )}
                    </span>
                  ))}
                </div>
                <span className="mono text-xs text-slate-600">
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </PageShell>
  );
}
