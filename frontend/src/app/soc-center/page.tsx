"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Select } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface SocEvent {
  id: number;
  source: string;
  event_type: string;
  source_ip: string | null;
  detail: string;
  created_at: string;
}

interface Alert {
  id: number;
  event_id: number | null;
  title: string;
  severity: string;
  status: string;
  rule_id: number | null;
  detail: string;
  created_at: string;
}

type AlertStatus = "open" | "acknowledged" | "closed";

const STATUS_TABS: AlertStatus[] = ["open", "acknowledged", "closed"];

export default function SocCenterPage() {
  const { isAnalystOrAbove } = useAuth();
  const [statusFilter, setStatusFilter] = useState<AlertStatus>("open");
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const {
    data: events,
    loading: eventsLoading,
    error: eventsError,
  } = usePolling(() => apiClient.get<SocEvent[]>("/api/soc/events"), []);

  const {
    data: alerts,
    loading: alertsLoading,
    error: alertsError,
    refetch: refetchAlerts,
  } = usePolling(
    () =>
      apiClient.get<Alert[]>(
        `/api/soc/alerts?status_filter=${statusFilter}`
      ),
    [statusFilter]
  );

  async function handleStatusChange(alertId: number, newStatus: AlertStatus) {
    setUpdatingId(alertId);
    setUpdateError(null);
    try {
      await apiClient.patch(`/api/soc/alerts/${alertId}`, {
        status: newStatus,
      });
      refetchAlerts();
    } catch (e) {
      setUpdateError(
        e instanceof ApiError ? e.message : "Failed to update alert status"
      );
    } finally {
      setUpdatingId(null);
    }
  }

  const eventColumns: Column<SocEvent>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "source", header: "Source" },
    { key: "event_type", header: "Event Type" },
    { key: "source_ip", header: "Source IP", mono: true },
    { key: "detail", header: "Detail" },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  const alertColumns: Column<Alert>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "title", header: "Title" },
    { key: "severity", header: "Severity", badge: true },
    { key: "status", header: "Status", badge: true },
    {
      key: "rule_id",
      header: "Rule",
      mono: true,
      render: (row) => (row.rule_id ? `#${row.rule_id}` : "—"),
    },
    { key: "detail", header: "Detail" },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    ...(isAnalystOrAbove
      ? [
          {
            key: "actions",
            header: "Action",
            render: (row: Alert) => (
              <Select
                value={row.status}
                disabled={updatingId === row.id}
                onChange={(e) =>
                  handleStatusChange(row.id, e.target.value as AlertStatus)
                }
                className="w-36"
              >
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="closed">Closed</option>
              </Select>
            ),
          } as Column<Alert>,
        ]
      : []),
  ];

  return (
    <PageShell
      title="SOC Center"
      description="Live security event feed and alert triage — auto-refreshing every 10s"
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Live Event Feed">
          <DataTable
            columns={eventColumns}
            rows={events || []}
            keyField="id"
            loading={eventsLoading}
            error={eventsError}
            emptyMessage="No events recorded."
          />
        </Card>

        <Card
          title="Alerts"
          action={
            <div className="flex items-center gap-1">
              {STATUS_TABS.map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`rounded-md border px-3 py-1 text-xs font-medium capitalize transition-colors ${
                    statusFilter === s
                      ? "border-blue-500 bg-blue-600/20 text-blue-300"
                      : "border-[#1e2530] bg-[#11161d] text-slate-400 hover:bg-[#171d26]"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          }
        >
          {updateError && (
            <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {updateError}
            </div>
          )}
          {!isAnalystOrAbove && (
            <div className="mb-3 text-xs text-slate-500">
              Viewer role: alert status updates are read-only.
            </div>
          )}
          <DataTable
            columns={alertColumns}
            rows={alerts || []}
            keyField="id"
            loading={alertsLoading}
            error={alertsError}
            emptyMessage={`No ${statusFilter} alerts.`}
          />
        </Card>
      </div>
    </PageShell>
  );
}
