"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Input, Textarea, Select, Label } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface Control {
  id: number;
  framework_id: number;
  code: string;
  title: string;
  status: "not_assessed" | "compliant" | "gap" | string;
}

interface RiskItem {
  id: number;
  title: string;
  description: string | null;
  likelihood: number;
  impact: number;
  status: string;
  created_at: string;
}

const CONTROL_STATUSES = ["not_assessed", "compliant", "gap"];

export default function GrcPage() {
  const { isAnalystOrAbove } = useAuth();
  const [updatingControlId, setUpdatingControlId] = useState<number | null>(
    null
  );
  const [controlError, setControlError] = useState<string | null>(null);

  const [riskTitle, setRiskTitle] = useState("");
  const [riskDescription, setRiskDescription] = useState("");
  const [riskLikelihood, setRiskLikelihood] = useState("3");
  const [riskImpact, setRiskImpact] = useState("3");
  const [submittingRisk, setSubmittingRisk] = useState(false);
  const [riskError, setRiskError] = useState<string | null>(null);

  const {
    data: controls,
    loading: controlsLoading,
    error: controlsError,
    refetch: refetchControls,
  } = usePolling(() => apiClient.get<Control[]>("/api/grc/controls"), [], {
    intervalMs: 20000,
  });

  const {
    data: riskRegister,
    loading: riskLoading,
    error: riskLoadError,
    refetch: refetchRiskRegister,
  } = usePolling(
    () => apiClient.get<RiskItem[]>("/api/grc/risk-register"),
    [],
    { intervalMs: 20000 }
  );

  async function handleControlStatusChange(control: Control, newStatus: string) {
    setUpdatingControlId(control.id);
    setControlError(null);
    try {
      await apiClient.patch(`/api/grc/controls/${control.id}`, {
        status: newStatus,
      });
      refetchControls();
    } catch (e) {
      setControlError(
        e instanceof ApiError ? e.message : "Failed to update control status"
      );
    } finally {
      setUpdatingControlId(null);
    }
  }

  async function handleAddRisk() {
    if (!riskTitle.trim()) return;
    setSubmittingRisk(true);
    setRiskError(null);
    try {
      await apiClient.post("/api/grc/risk-register", {
        title: riskTitle.trim(),
        description: riskDescription.trim() || undefined,
        likelihood: Number(riskLikelihood),
        impact: Number(riskImpact),
      });
      setRiskTitle("");
      setRiskDescription("");
      setRiskLikelihood("3");
      setRiskImpact("3");
      refetchRiskRegister();
    } catch (e) {
      setRiskError(
        e instanceof ApiError ? e.message : "Failed to add risk item"
      );
    } finally {
      setSubmittingRisk(false);
    }
  }

  const controlColumns: Column<Control>[] = [
    { key: "code", header: "Code", mono: true, width: "100px" },
    { key: "title", header: "Title" },
    { key: "framework_id", header: "Framework", mono: true, width: "100px" },
    {
      key: "status",
      header: "Status",
      render: (row) => {
        if (isAnalystOrAbove) {
          return (
            <Select
              value={row.status}
              disabled={updatingControlId === row.id}
              onChange={(e) => handleControlStatusChange(row, e.target.value)}
              className="w-40"
            >
              {CONTROL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          );
        }
        return <Badge variant={row.status}>{row.status}</Badge>;
      },
    },
  ];

  const riskColumns: Column<RiskItem>[] = [
    { key: "title", header: "Title" },
    {
      key: "description",
      header: "Description",
      render: (row) => row.description || "—",
    },
    { key: "likelihood", header: "Likelihood", mono: true, width: "90px" },
    { key: "impact", header: "Impact", mono: true, width: "80px" },
    {
      key: "risk_score",
      header: "Risk Score",
      mono: true,
      width: "90px",
      render: (row) => row.likelihood * row.impact,
    },
    { key: "status", header: "Status", badge: true },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  return (
    <PageShell
      title="GRC"
      description="Governance, risk and compliance: framework controls and risk register"
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Framework Compliance Checklist">
          {controlError && (
            <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {controlError}
            </div>
          )}
          <DataTable
            columns={controlColumns}
            rows={controls || []}
            keyField="id"
            loading={controlsLoading}
            error={controlsError}
            emptyMessage="No controls found."
          />
          {!isAnalystOrAbove && (
            <div className="mt-2 text-xs text-slate-500">
              Viewer role: control status changes are read-only.
            </div>
          )}
        </Card>

        <Card title="Risk Register">
          <DataTable
            columns={riskColumns}
            rows={riskRegister || []}
            keyField="id"
            loading={riskLoading}
            error={riskLoadError}
            emptyMessage="No risks recorded."
          />

          {isAnalystOrAbove ? (
            <div className="mt-4 border-t border-[#1e2530] pt-4">
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Add Risk
              </h4>
              {riskError && (
                <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {riskError}
                </div>
              )}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Label>Title</Label>
                  <Input
                    value={riskTitle}
                    onChange={(e) => setRiskTitle(e.target.value)}
                    placeholder="Risk title"
                  />
                </div>
                <div className="sm:col-span-2">
                  <Label>Description (optional)</Label>
                  <Textarea
                    rows={2}
                    value={riskDescription}
                    onChange={(e) => setRiskDescription(e.target.value)}
                    placeholder="Describe the risk..."
                  />
                </div>
                <div>
                  <Label>Likelihood (1-5)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={5}
                    value={riskLikelihood}
                    onChange={(e) => setRiskLikelihood(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Impact (1-5)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={5}
                    value={riskImpact}
                    onChange={(e) => setRiskImpact(e.target.value)}
                  />
                </div>
              </div>
              <div className="mt-3 flex justify-end">
                <Button
                  onClick={handleAddRisk}
                  disabled={submittingRisk || !riskTitle.trim()}
                >
                  {submittingRisk ? "Adding..." : "Add Risk"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-3 text-xs text-slate-500">
              Viewer role: adding risks is disabled.
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
