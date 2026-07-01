"use client";

import { PageShell } from "@/components/PageShell";
import { Card, StatCard } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface ChecklistItem {
  cve_id: string;
  title: string;
  severity: string;
  note: string;
}

interface ChecklistResponse {
  items: ChecklistItem[];
}

type LynisScan = Record<string, unknown> | null;

export default function VulnerabilitiesPage() {
  const {
    data: checklist,
    loading: checklistLoading,
    error: checklistError,
  } = usePolling(
    () => apiClient.get<ChecklistResponse>("/api/vulnerabilities/cve-checklist"),
    [],
    { intervalMs: 30000 }
  );

  const {
    data: lynisScan,
    loading: lynisLoading,
    error: lynisError,
  } = usePolling(
    () => apiClient.get<LynisScan>("/api/vulnerabilities/latest-lynis-scan"),
    [],
    { intervalMs: 30000 }
  );

  const columns: Column<ChecklistItem>[] = [
    { key: "cve_id", header: "CVE ID", mono: true },
    { key: "title", header: "Title" },
    { key: "severity", header: "Severity", badge: true },
    { key: "note", header: "Note" },
  ];

  const rawOutput =
    lynisScan &&
    ("raw_output" in lynisScan
      ? (lynisScan.raw_output as unknown)
      : "output" in lynisScan
      ? (lynisScan.output as unknown)
      : undefined);

  return (
    <PageShell
      title="Vulnerabilities"
      description="CVE checklist and system hardening scan results"
    >
      <Card title="CVE Checklist">
        <DataTable
          columns={columns}
          rows={checklist?.items || []}
          keyField="cve_id"
          loading={checklistLoading}
          error={checklistError}
          emptyMessage="No CVE checklist items available."
        />
      </Card>

      <div className="mt-6">
        <Card title="Latest Lynis Scan">
          {lynisLoading && (
            <div className="py-6 text-center text-sm text-slate-500">
              Loading...
            </div>
          )}
          {!lynisLoading && lynisError && (
            <div className="py-6 text-center text-sm text-red-400">
              {lynisError}
            </div>
          )}
          {!lynisLoading && !lynisError && !lynisScan && (
            <div className="py-6 text-center text-sm text-slate-500">
              No Lynis scan has been run yet.
            </div>
          )}
          {!lynisLoading && !lynisError && lynisScan && (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {"id" in lynisScan && (
                  <StatCard
                    label="Scan ID"
                    value={String(lynisScan.id ?? "—")}
                  />
                )}
                {"status" in lynisScan && (
                  <StatCard
                    label="Status"
                    value={String(lynisScan.status ?? "—")}
                  />
                )}
                {"warnings_count" in lynisScan && (
                  <StatCard
                    label="Warnings"
                    value={String(lynisScan.warnings_count ?? "—")}
                    accent="medium"
                  />
                )}
                {"hardening_index" in lynisScan && (
                  <StatCard
                    label="Hardening Index"
                    value={String(lynisScan.hardening_index ?? "—")}
                    accent="low"
                  />
                )}
              </div>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 text-xs text-slate-500">
                {"tool" in lynisScan && (
                  <div>
                    Tool:{" "}
                    <span className="mono text-slate-300">
                      {String(lynisScan.tool)}
                    </span>
                  </div>
                )}
                {"created_at" in lynisScan && lynisScan.created_at != null && (
                  <div>
                    Created:{" "}
                    <span className="mono text-slate-300">
                      {new Date(String(lynisScan.created_at)).toLocaleString()}
                    </span>
                  </div>
                )}
                {"finished_at" in lynisScan && lynisScan.finished_at != null && (
                  <div>
                    Finished:{" "}
                    <span className="mono text-slate-300">
                      {new Date(String(lynisScan.finished_at)).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
              {rawOutput != null && (
                <div>
                  <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                    Raw Output
                  </div>
                  <pre className="mono text-xs whitespace-pre-wrap bg-black/40 border border-[#1e2530] rounded-md p-3 max-h-96 overflow-y-auto">
                    {typeof rawOutput === "string"
                      ? rawOutput
                      : JSON.stringify(rawOutput, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
