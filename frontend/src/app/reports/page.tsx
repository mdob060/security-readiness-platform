"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Select, Label } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface ReportItem {
  id: number;
  report_type: string;
  status: string;
  file_path: string | null;
  created_at: string;
  completed_at: string | null;
}

const REPORT_TYPES = ["incidents", "compliance", "executive"];

export default function ReportsPage() {
  const { isAnalystOrAbove } = useAuth();
  const [reportType, setReportType] = useState(REPORT_TYPES[0]);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    data: reports,
    loading,
    error,
    refetch,
  } = usePolling(() => apiClient.get<ReportItem[]>("/api/reports"), [], {
    intervalMs: 5000,
  });

  async function handleQueueReport() {
    setSubmitting(true);
    setFormError(null);
    try {
      await apiClient.post("/api/reports", { report_type: reportType });
      refetch();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "Failed to queue report");
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<ReportItem>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "report_type", header: "Type" },
    { key: "status", header: "Status", badge: true },
    {
      key: "file_path",
      header: "File",
      render: (row) =>
        row.file_path ? (
          <Badge variant="completed">Completed</Badge>
        ) : (
          <span className="text-slate-500">Pending</span>
        ),
    },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: "completed_at",
      header: "Completed At",
      mono: true,
      render: (row) =>
        row.completed_at ? new Date(row.completed_at).toLocaleString() : "—",
    },
  ];

  return (
    <PageShell
      title="Reports"
      description="Generate and track compliance, incident, and executive reports"
      actions={
        <Button variant="secondary" onClick={refetch}>
          Refresh
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Reports">
          <DataTable
            columns={columns}
            rows={reports || []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No reports queued yet."
          />
        </Card>

        {isAnalystOrAbove ? (
          <Card title="Queue New Report">
            {formError && (
              <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {formError}
              </div>
            )}
            <div className="max-w-xs">
              <Label>Report Type</Label>
              <Select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
              >
                {REPORT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
            </div>
            <div className="mt-3 flex justify-end">
              <Button onClick={handleQueueReport} disabled={submitting}>
                {submitting ? "Queuing..." : "Queue Report"}
              </Button>
            </div>
          </Card>
        ) : (
          <div className="text-xs text-slate-500">
            Viewer role: queuing new reports is disabled.
          </div>
        )}
      </div>
    </PageShell>
  );
}
