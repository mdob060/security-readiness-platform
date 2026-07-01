"use client";

import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { CircularGauge } from "@/components/Gauge";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface PciControl {
  requirement_code: string;
  description: string;
  check_type: string;
  status: string;
  detail: string;
}

interface PciReport {
  compliance_percentage: number;
  controls: PciControl[];
}

export default function PciDssPage() {
  const {
    data: report,
    loading,
    error,
  } = usePolling(() => apiClient.get<PciReport>("/api/pci-dss/report"), [], {
    intervalMs: 30000,
  });

  const columns: Column<PciControl>[] = [
    { key: "requirement_code", header: "Requirement", mono: true },
    { key: "description", header: "Description" },
    { key: "check_type", header: "Check Type" },
    { key: "status", header: "Status", badge: true },
    { key: "detail", header: "Detail" },
  ];

  return (
    <PageShell
      title="PCI-DSS Compliance"
      description="Payment Card Industry Data Security Standard control checks"
    >
      <Card>
        <div className="flex items-center justify-center py-4">
          {loading ? (
            <div className="text-sm text-slate-500">Loading...</div>
          ) : error ? (
            <div className="text-sm text-red-400">{error}</div>
          ) : (
            <CircularGauge
              value={report?.compliance_percentage ?? 0}
              label="PCI-DSS Compliance"
            />
          )}
        </div>
      </Card>

      <div className="mt-6">
        <Card title="Controls">
          <DataTable
            columns={columns}
            rows={report?.controls || []}
            keyField="requirement_code"
            loading={loading}
            error={error}
            emptyMessage="No PCI-DSS controls available."
          />
        </Card>
      </div>
    </PageShell>
  );
}
