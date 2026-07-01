"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Textarea, Label } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

type TargetStatus = "pending" | "approved" | "rejected" | "revoked";

interface ScanTarget {
  id: number;
  target: string;
  justification: string;
  status: TargetStatus;
  requested_by_id: number;
  approved_by_id: number | null;
  created_at: string;
}

export default function ScanScopePage() {
  const { isAdmin } = useAuth();

  const {
    data: targets,
    loading,
    error,
    refetch,
  } = usePolling(() => apiClient.get<ScanTarget[]>("/api/scan-scope/targets"), [], {
    intervalMs: 15000,
  });

  const [target, setTarget] = useState("");
  const [justification, setJustification] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [actioningId, setActioningId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!target.trim() || !justification.trim()) {
      setFormError("Target and justification are both required.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/scan-scope/targets", {
        target: target.trim(),
        justification: justification.trim(),
      });
      setTarget("");
      setJustification("");
      refetch();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAction(id: number, action: "approve" | "reject" | "revoke") {
    setActionError(null);
    setActioningId(id);
    try {
      await apiClient.post(`/api/scan-scope/targets/${id}/${action}`);
      refetch();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : `Failed to ${action} target.`);
    } finally {
      setActioningId(null);
    }
  }

  const columns: Column<ScanTarget>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "target", header: "Target", mono: true },
    { key: "justification", header: "Justification" },
    { key: "status", header: "Status", badge: true, width: "110px" },
    { key: "requested_by_id", header: "Requested By", mono: true, width: "110px" },
    {
      key: "created_at",
      header: "Requested At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: "actions",
      header: "Actions",
      width: "220px",
      render: (row) => {
        if (!isAdmin) {
          return <span className="text-slate-600 text-xs">Admin only</span>;
        }
        const busy = actioningId === row.id;
        if (row.status === "pending") {
          return (
            <div className="flex gap-2">
              <Button
                variant="success"
                disabled={busy}
                onClick={() => handleAction(row.id, "approve")}
              >
                Approve
              </Button>
              <Button
                variant="danger"
                disabled={busy}
                onClick={() => handleAction(row.id, "reject")}
              >
                Reject
              </Button>
            </div>
          );
        }
        if (row.status === "approved") {
          return (
            <Button
              variant="danger"
              disabled={busy}
              onClick={() => handleAction(row.id, "revoke")}
            >
              Revoke
            </Button>
          );
        }
        return <span className="text-slate-600 text-xs">—</span>;
      },
    },
  ];

  return (
    <PageShell
      title="Scan Scope"
      description="Authorization gate for red-team scan targets — request, approve, reject, or revoke scope"
    >
      <div className="flex flex-col gap-6">
        <RoleGate
          allow={["admin", "analyst"]}
          fallback={
            <Card title="Request New Target">
              <p className="text-sm text-slate-500">
                Viewers cannot request new scan targets. Contact an analyst or admin.
              </p>
            </Card>
          }
        >
          <Card title="Request New Target">
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              {formError && (
                <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {formError}
                </div>
              )}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <Label>Target</Label>
                  <Input
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="e.g. 10.0.0.15 or scan.example.com"
                  />
                </div>
                <div>
                  <Label>Justification</Label>
                  <Textarea
                    value={justification}
                    onChange={(e) => setJustification(e.target.value)}
                    placeholder="Why is this scan authorized?"
                    rows={1}
                  />
                </div>
              </div>
              <div>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Submitting..." : "Submit Request"}
                </Button>
              </div>
            </form>
          </Card>
        </RoleGate>

        {actionError && (
          <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {actionError}
          </div>
        )}

        <Card title="Scan Targets">
          <DataTable
            columns={columns}
            rows={targets ?? []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No scan targets requested yet."
          />
        </Card>
      </div>
    </PageShell>
  );
}
