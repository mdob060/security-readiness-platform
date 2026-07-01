"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Decision {
  id: number;
  alert_id: number;
  recommended_action: string;
  rationale: string;
  status: "pending" | "approved" | "rejected" | string;
  reviewed_by_id: number | null;
  created_at: string;
}

export default function AutomationPage() {
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  const {
    data: decisions,
    loading,
    error,
    refetch,
  } = usePolling(
    () => apiClient.get<Decision[]>("/api/automation/decisions"),
    [],
    { intervalMs: 15000 }
  );

  const review = async (id: number, approve: boolean) => {
    setReviewingId(id);
    setReviewError(null);
    try {
      await apiClient.post(`/api/automation/decisions/${id}/review`, {
        approve,
      });
      refetch();
    } catch (e) {
      setReviewError(
        e instanceof ApiError ? e.message : "Failed to submit review"
      );
    } finally {
      setReviewingId(null);
    }
  };

  const all = decisions ?? [];
  const pending = all
    .filter((d) => d.status === "pending")
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  const reviewed = all
    .filter((d) => d.status !== "pending")
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

  return (
    <PageShell
      title="Automation"
      description="Review SOAR decisions recommended by the automated response engine"
    >
      {loading && (
        <div className="py-6 text-center text-sm text-slate-500">
          Loading decisions...
        </div>
      )}
      {error && (
        <div className="rounded-md border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}
      {reviewError && (
        <div className="mb-4 rounded-md border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {reviewError}
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="mb-6">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Pending Review ({pending.length})
            </h2>
            {pending.length === 0 ? (
              <div className="rounded-lg border border-[#1e2530] bg-[#0d1117] p-6 text-center text-sm text-slate-500">
                No pending decisions. All caught up.
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {pending.map((d) => (
                  <Card key={d.id}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-2">
                          <span className="mono text-xs text-slate-500">
                            decision #{d.id}
                          </span>
                          <span className="mono text-xs text-slate-500">
                            alert #{d.alert_id}
                          </span>
                          <Badge variant={d.status}>{d.status}</Badge>
                        </div>
                        <div className="mb-1 text-sm font-medium text-slate-200">
                          {d.recommended_action}
                        </div>
                        <div className="text-xs text-slate-500">
                          {d.rationale}
                        </div>
                        <div className="mt-2 mono text-xs text-slate-600">
                          {new Date(d.created_at).toLocaleString()}
                        </div>
                      </div>
                      <RoleGate
                        allow={["admin", "analyst"]}
                        fallback={
                          <span className="text-xs text-slate-600">
                            Viewer — read only
                          </span>
                        }
                      >
                        <div className="flex shrink-0 gap-2">
                          <Button
                            variant="success"
                            disabled={reviewingId === d.id}
                            onClick={() => review(d.id, true)}
                          >
                            Approve
                          </Button>
                          <Button
                            variant="danger"
                            disabled={reviewingId === d.id}
                            onClick={() => review(d.id, false)}
                          >
                            Reject
                          </Button>
                        </div>
                      </RoleGate>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <div>
            <button
              onClick={() => setHistoryOpen((v) => !v)}
              className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-300"
            >
              <span>{historyOpen ? "▾" : "▸"}</span>
              History ({reviewed.length})
            </button>
            {historyOpen && (
              <div className="flex flex-col gap-3">
                {reviewed.length === 0 ? (
                  <div className="rounded-lg border border-[#1e2530] bg-[#0d1117] p-6 text-center text-sm text-slate-500">
                    No reviewed decisions yet.
                  </div>
                ) : (
                  reviewed.map((d) => (
                    <Card key={d.id} className="opacity-80">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="mb-2 flex items-center gap-2">
                            <span className="mono text-xs text-slate-500">
                              decision #{d.id}
                            </span>
                            <span className="mono text-xs text-slate-500">
                              alert #{d.alert_id}
                            </span>
                            <Badge variant={d.status}>{d.status}</Badge>
                          </div>
                          <div className="mb-1 text-sm font-medium text-slate-200">
                            {d.recommended_action}
                          </div>
                          <div className="text-xs text-slate-500">
                            {d.rationale}
                          </div>
                          <div className="mt-2 mono text-xs text-slate-600">
                            {new Date(d.created_at).toLocaleString()}
                            {d.reviewed_by_id != null &&
                              ` · reviewed by user #${d.reviewed_by_id}`}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            )}
          </div>
        </>
      )}
    </PageShell>
  );
}
