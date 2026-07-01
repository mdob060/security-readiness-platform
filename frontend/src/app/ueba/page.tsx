"use client";

import { useMemo, useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Input, Label } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Entity {
  id: number;
  entity_name: string;
  entity_type: string;
  risk_score: number;
  updated_at: string;
}

function riskVariant(score: number): string {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "medium";
  return "low";
}

export default function UebaPage() {
  const { isAnalystOrAbove } = useAuth();

  const {
    data: entities,
    loading,
    error,
    refetch,
  } = usePolling<Entity[]>(() => apiClient.get<Entity[]>("/api/ueba/entities"), []);

  const sortedEntities = useMemo(
    () => [...(entities ?? [])].sort((a, b) => b.risk_score - a.risk_score),
    [entities]
  );

  const [form, setForm] = useState({ entity_name: "", action: "", value: "" });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const columns: Column<Entity>[] = [
    { key: "entity_name", header: "Entity" },
    { key: "entity_type", header: "Type" },
    {
      key: "risk_score",
      header: "Risk Score",
      render: (row) => (
        <Badge variant={riskVariant(row.risk_score)}>{row.risk_score.toFixed(0)}</Badge>
      ),
    },
    {
      key: "updated_at",
      header: "Updated",
      mono: true,
      render: (row) => new Date(row.updated_at).toLocaleString(),
    },
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);
    const valueNum = Number(form.value);
    if (!form.entity_name || !form.action || form.value === "" || Number.isNaN(valueNum)) {
      setFormError("Please fill in all required fields with valid values.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/ueba/events", {
        entity_name: form.entity_name,
        action: form.action,
        value: valueNum,
      });
      setSuccessMsg("Behavior event submitted.");
      setForm({ entity_name: "", action: "", value: "" });
      refetch();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to submit event.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="UEBA"
      description="User and entity behavior analytics"
    >
      <div className="flex flex-col gap-6">
        {isAnalystOrAbove && (
          <Card title="Submit Behavior Event">
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <Label>Entity Name</Label>
                <Input
                  value={form.entity_name}
                  onChange={(e) => setForm({ ...form, entity_name: e.target.value })}
                  placeholder="jdoe"
                  required
                />
              </div>
              <div>
                <Label>Action</Label>
                <Input
                  value={form.action}
                  onChange={(e) => setForm({ ...form, action: e.target.value })}
                  placeholder="login_failed"
                  required
                />
              </div>
              <div>
                <Label>Value</Label>
                <Input
                  type="number"
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: e.target.value })}
                  placeholder="1"
                  required
                />
              </div>
              <div className="col-span-full flex items-center gap-3">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Submitting..." : "Submit Event"}
                </Button>
                {formError && <span className="text-sm text-red-400">{formError}</span>}
                {successMsg && <span className="text-sm text-green-400">{successMsg}</span>}
              </div>
            </form>
          </Card>
        )}

        <Card title="Entities (by Risk Score)">
          <DataTable
            columns={columns}
            rows={sortedEntities}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No entities tracked yet."
          />
        </Card>
      </div>
    </PageShell>
  );
}
