"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card, StatCard } from "@/components/Card";
import { ProgressBar } from "@/components/Gauge";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Select } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface SystemResources {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  load_average: [number, number, number];
  boot_time: number;
}

interface Fail2ban {
  jail: string;
  currently_failed: number;
  total_failed: number;
  currently_banned: number;
  total_banned: number;
  banned_ips: string[];
}

type ScanStatus = "queued" | "running" | "completed" | "failed";

interface BlueTeamScan {
  id: number;
  tool: string;
  status: ScanStatus;
  warnings_count: number | null;
  hardening_index: number | null;
  created_at: string;
  finished_at: string | null;
}

interface BlueTeamScanDetail extends BlueTeamScan {
  raw_output: string | null;
}

export default function BlueTeamPage() {
  const { data: resources, loading: resourcesLoading } = usePolling(
    () => apiClient.get<SystemResources>("/api/blue-team/system-resources"),
    [],
    { intervalMs: 10000 }
  );

  const { data: fail2ban, loading: fail2banLoading } = usePolling(
    () => apiClient.get<Fail2ban>("/api/blue-team/fail2ban"),
    [],
    { intervalMs: 10000 }
  );

  const { data: toolsData } = usePolling(
    () => apiClient.get<{ tools: string[] }>("/api/blue-team/tools"),
    [],
    { intervalMs: 60000 }
  );

  const {
    data: scans,
    loading: scansLoading,
    error: scansError,
    refetch: refetchScans,
  } = usePolling(() => apiClient.get<BlueTeamScan[]>("/api/blue-team/scans"), [], {
    intervalMs: 10000,
  });

  const [selectedScanId, setSelectedScanId] = useState<number | null>(null);
  const {
    data: scanDetail,
    loading: detailLoading,
    error: detailError,
  } = usePolling(
    () => {
      if (selectedScanId === null) return Promise.resolve(null as unknown as BlueTeamScanDetail);
      return apiClient.get<BlueTeamScanDetail>(`/api/blue-team/scans/${selectedScanId}`);
    },
    [selectedScanId],
    { intervalMs: 5000, enabled: selectedScanId !== null }
  );

  const [tool, setTool] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleRunScan(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!tool) {
      setFormError("Select a tool to run.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/blue-team/scans", { tool });
      refetchScans();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "Failed to run scan.");
    } finally {
      setSubmitting(false);
    }
  }

  const scanColumns: Column<BlueTeamScan>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "tool", header: "Tool", mono: true, width: "120px" },
    { key: "status", header: "Status", badge: true, width: "100px" },
    {
      key: "warnings_count",
      header: "Warnings",
      width: "100px",
      render: (row) => row.warnings_count ?? <span className="text-slate-600">—</span>,
    },
    {
      key: "hardening_index",
      header: "Hardening Index",
      width: "130px",
      render: (row) =>
        row.hardening_index !== null ? (
          row.hardening_index
        ) : (
          <span className="text-slate-600">—</span>
        ),
    },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  return (
    <PageShell
      title="Blue Team"
      description="Defensive operations — system health, intrusion prevention, and hardening scans"
    >
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card title="System Resources">
            {resourcesLoading && !resources ? (
              <p className="text-sm text-slate-500">Loading...</p>
            ) : resources ? (
              <div className="flex flex-col gap-4">
                <ProgressBar label="CPU" value={resources.cpu_percent} />
                <ProgressBar label="Memory" value={resources.memory_percent} />
                <ProgressBar label="Disk" value={resources.disk_percent} />
                <div className="grid grid-cols-3 gap-2 pt-2 text-center">
                  <div>
                    <div className="mono text-lg text-slate-200">
                      {resources.load_average[0].toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500">1m load</div>
                  </div>
                  <div>
                    <div className="mono text-lg text-slate-200">
                      {resources.load_average[1].toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500">5m load</div>
                  </div>
                  <div>
                    <div className="mono text-lg text-slate-200">
                      {resources.load_average[2].toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500">15m load</div>
                  </div>
                </div>
                <div className="text-xs text-slate-500">
                  System up since{" "}
                  <span className="text-slate-300">
                    {new Date(resources.boot_time * 1000).toLocaleString()}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No data available.</p>
            )}
          </Card>

          <Card title="Fail2ban">
            {fail2banLoading && !fail2ban ? (
              <p className="text-sm text-slate-500">Loading...</p>
            ) : fail2ban ? (
              <div className="flex flex-col gap-4">
                <div className="text-xs text-slate-500">
                  Jail: <span className="mono text-slate-300">{fail2ban.jail}</span>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard label="Currently Failed" value={fail2ban.currently_failed} accent="medium" />
                  <StatCard label="Total Failed" value={fail2ban.total_failed} />
                  <StatCard label="Currently Banned" value={fail2ban.currently_banned} accent="high" />
                  <StatCard label="Total Banned" value={fail2ban.total_banned} />
                </div>
                <div>
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Banned IPs
                  </h4>
                  {fail2ban.banned_ips.length === 0 ? (
                    <p className="text-sm text-slate-500">No IPs currently banned.</p>
                  ) : (
                    <ul className="flex flex-col gap-1">
                      {fail2ban.banned_ips.map((ip) => (
                        <li
                          key={ip}
                          className="mono rounded border border-[#1e2530] px-2 py-1 text-xs text-slate-300"
                        >
                          {ip}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No data available.</p>
            )}
          </Card>
        </div>

        <RoleGate
          allow={["admin", "analyst"]}
          fallback={
            <Card title="Run Scan">
              <p className="text-sm text-slate-500">
                Viewers cannot run hardening scans. Contact an analyst or admin.
              </p>
            </Card>
          }
        >
          <Card title="Run Scan">
            <form onSubmit={handleRunScan} className="flex flex-wrap items-end gap-3">
              {formError && (
                <div className="w-full rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                  {formError}
                </div>
              )}
              <div className="w-56">
                <Select value={tool} onChange={(e) => setTool(e.target.value)}>
                  <option value="">Select a tool...</option>
                  {(toolsData?.tools ?? []).map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Running..." : "Run Scan"}
              </Button>
            </form>
          </Card>
        </RoleGate>

        <Card title="Hardening Scans">
          <DataTable
            columns={scanColumns}
            rows={scans ?? []}
            keyField="id"
            loading={scansLoading}
            error={scansError}
            emptyMessage="No scans have been run yet."
            onRowClick={(row) => setSelectedScanId(row.id)}
          />
        </Card>

        {selectedScanId !== null && (
          <Card
            title={`Scan #${selectedScanId} Detail`}
            action={
              <Button variant="ghost" onClick={() => setSelectedScanId(null)}>
                Close
              </Button>
            }
          >
            {detailLoading && !scanDetail && (
              <p className="text-sm text-slate-500">Loading scan detail...</p>
            )}
            {detailError && <p className="text-sm text-red-400">{detailError}</p>}
            {scanDetail && (
              <pre className="mono text-xs whitespace-pre-wrap bg-black/40 border border-[#1e2530] rounded-md p-3 max-h-96 overflow-y-auto">
                {scanDetail.raw_output || "(no output)"}
              </pre>
            )}
          </Card>
        )}
      </div>
    </PageShell>
  );
}
