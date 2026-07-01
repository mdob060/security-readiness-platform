"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Select, Label } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

type JobStatus = "queued" | "running" | "completed" | "failed";

interface RedTeamJob {
  id: number;
  target_id: number;
  tool: string;
  status: JobStatus;
  exit_code: number | null;
  summary: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

interface Finding {
  id: number;
  severity: string;
  title: string;
  detail: string | null;
}

interface RedTeamJobDetail extends RedTeamJob {
  raw_output: string | null;
  findings: Finding[];
}

interface ScanTarget {
  id: number;
  target: string;
  justification: string;
  status: string;
  requested_by_id: number;
  approved_by_id: number | null;
  created_at: string;
}

export default function RedTeamPage() {
  const {
    data: jobs,
    loading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = usePolling(() => apiClient.get<RedTeamJob[]>("/api/red-team/jobs"), [], {
    intervalMs: 7000,
  });

  const { data: toolsData } = usePolling(
    () => apiClient.get<{ tools: string[] }>("/api/red-team/tools"),
    [],
    { intervalMs: 60000 }
  );

  const { data: targetsData } = usePolling(
    () => apiClient.get<ScanTarget[]>("/api/scan-scope/targets"),
    [],
    { intervalMs: 15000 }
  );

  const approvedTargets = useMemo(
    () => (targetsData ?? []).filter((t) => t.status === "approved"),
    [targetsData]
  );

  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const {
    data: jobDetail,
    loading: detailLoading,
    error: detailError,
  } = usePolling(
    () => {
      if (selectedJobId === null) return Promise.resolve(null as unknown as RedTeamJobDetail);
      return apiClient.get<RedTeamJobDetail>(`/api/red-team/jobs/${selectedJobId}`);
    },
    [selectedJobId],
    { intervalMs: 5000, enabled: selectedJobId !== null }
  );

  const [targetId, setTargetId] = useState<string>("");
  const [tool, setTool] = useState<string>("");
  const [service, setService] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!targetId || !tool) {
      setFormError("Target and tool are required.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/red-team/jobs", {
        target_id: Number(targetId),
        tool,
        ...(service.trim() ? { service: service.trim() } : {}),
      });
      setService("");
      refetchJobs();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "Failed to create scan job.");
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<RedTeamJob>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "tool", header: "Tool", mono: true, width: "100px" },
    { key: "status", header: "Status", badge: true, width: "100px" },
    { key: "summary", header: "Summary" },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  return (
    <PageShell
      title="Red Team"
      description="Offensive security tooling — launch and review authorized scan jobs"
    >
      <div className="flex flex-col gap-6">
        <RoleGate
          allow={["admin", "analyst"]}
          fallback={
            <Card title="New Scan Job">
              <p className="text-sm text-slate-500">
                Viewers cannot launch scan jobs. Contact an analyst or admin.
              </p>
            </Card>
          }
        >
          <Card title="New Scan Job">
            {approvedTargets.length === 0 ? (
              <p className="text-sm text-slate-500">
                No approved scan targets.{" "}
                <Link href="/scan-scope" className="text-blue-400 hover:underline">
                  Go request one.
                </Link>
              </p>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                {formError && (
                  <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                    {formError}
                  </div>
                )}
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div>
                    <Label>Target</Label>
                    <Select value={targetId} onChange={(e) => setTargetId(e.target.value)}>
                      <option value="">Select a target...</option>
                      {approvedTargets.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.target} (#{t.id})
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Label>Tool</Label>
                    <Select value={tool} onChange={(e) => setTool(e.target.value)}>
                      <option value="">Select a tool...</option>
                      {(toolsData?.tools ?? []).map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Label>Service (optional)</Label>
                    <Input
                      value={service}
                      onChange={(e) => setService(e.target.value)}
                      placeholder="e.g. http, ssh"
                    />
                  </div>
                </div>
                <div>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? "Launching..." : "Launch Scan"}
                  </Button>
                </div>
              </form>
            )}
          </Card>
        </RoleGate>

        <Card title="Scan Jobs">
          <DataTable
            columns={columns}
            rows={jobs ?? []}
            keyField="id"
            loading={jobsLoading}
            error={jobsError}
            emptyMessage="No scan jobs yet."
            onRowClick={(row) => setSelectedJobId(row.id)}
          />
        </Card>

        {selectedJobId !== null && (
          <Card
            title={`Job #${selectedJobId} Detail`}
            action={
              <Button variant="ghost" onClick={() => setSelectedJobId(null)}>
                Close
              </Button>
            }
          >
            {detailLoading && !jobDetail && (
              <p className="text-sm text-slate-500">Loading job detail...</p>
            )}
            {detailError && (
              <p className="text-sm text-red-400">{detailError}</p>
            )}
            {jobDetail && (
              <div className="flex flex-col gap-4">
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <Badge variant={jobDetail.status}>{jobDetail.status}</Badge>
                  <span className="mono text-slate-400">{jobDetail.tool}</span>
                  <span className="text-slate-500">
                    target #{jobDetail.target_id}
                  </span>
                  {jobDetail.exit_code !== null && (
                    <span className="mono text-slate-500">
                      exit code {jobDetail.exit_code}
                    </span>
                  )}
                </div>
                {jobDetail.summary && (
                  <p className="text-sm text-slate-300">{jobDetail.summary}</p>
                )}

                <div>
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Findings
                  </h4>
                  {jobDetail.findings.length === 0 ? (
                    <p className="text-sm text-slate-500">No findings reported.</p>
                  ) : (
                    <ul className="flex flex-col gap-2">
                      {jobDetail.findings.map((f) => (
                        <li
                          key={f.id}
                          className="rounded-md border border-[#1e2530] px-3 py-2 text-sm"
                        >
                          <div className="flex items-center gap-2">
                            <Badge variant={f.severity}>{f.severity}</Badge>
                            <span className="text-slate-200">{f.title}</span>
                          </div>
                          {f.detail && (
                            <p className="mt-1 text-xs text-slate-500">{f.detail}</p>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div>
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Raw Output
                  </h4>
                  <pre className="mono text-xs whitespace-pre-wrap bg-black/40 border border-[#1e2530] rounded-md p-3 max-h-96 overflow-y-auto">
                    {jobDetail.raw_output || "(no output)"}
                  </pre>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </PageShell>
  );
}
