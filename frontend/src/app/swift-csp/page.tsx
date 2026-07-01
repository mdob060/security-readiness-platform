"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Label, Select, Textarea } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Control {
  id: number;
  control_code: string;
  title: string;
  category: string;
  status: string;
}

const STATUSES = ["compliant", "gap", "not_assessed"];

export default function SwiftCspPage() {
  const { isAnalystOrAbove } = useAuth();

  const {
    data: controls,
    loading,
    error,
    refetch,
  } = usePolling<Control[]>(() => apiClient.get<Control[]>("/api/swift-csp/controls"), []);

  const [form, setForm] = useState({ control_id: "", status: "compliant", notes: "" });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const columns: Column<Control>[] = [
    { key: "control_code", header: "Code", mono: true },
    { key: "title", header: "Title" },
    { key: "category", header: "Category" },
    { key: "status", header: "Status", badge: true },
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);
    if (!form.control_id || !form.status) {
      setFormError("Please select a control and status.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/swift-csp/assessments", {
        control_id: Number(form.control_id),
        status: form.status,
        notes: form.notes || undefined,
      });
      setSuccessMsg("Assessment submitted.");
      setForm({ control_id: form.control_id, status: "compliant", notes: "" });
      refetch();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to submit assessment.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="SWIFT CSP"
      description="SWIFT Customer Security Programme controls"
    >
      <div className="flex flex-col gap-6">
        {isAnalystOrAbove && (
          <Card title="Submit Assessment">
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <Label>Control</Label>
                <Select
                  value={form.control_id}
                  onChange={(e) => setForm({ ...form, control_id: e.target.value })}
                  required
                >
                  <option value="">Select a control...</option>
                  {(controls ?? []).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.control_code} — {c.title}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Status</Label>
                <Select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Notes (optional)</Label>
                <Textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={1}
                  placeholder="Assessment notes..."
                />
              </div>
              <div className="col-span-full flex items-center gap-3">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Submitting..." : "Submit Assessment"}
                </Button>
                {formError && <span className="text-sm text-red-400">{formError}</span>}
                {successMsg && <span className="text-sm text-green-400">{successMsg}</span>}
              </div>
            </form>
          </Card>
        )}

        <Card title="Controls">
          <DataTable
            columns={columns}
            rows={controls ?? []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No controls found."
          />
        </Card>
      </div>
    </PageShell>
  );
}
