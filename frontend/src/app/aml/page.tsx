"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Label } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface WatchlistEntry {
  id: number;
  entity_type: string;
  country: string;
  full_name: string;
  list_source: string;
}

interface ScreenResult {
  query_name: string;
  matched_name: string;
  match_score: number;
  list_source: string;
}

export default function AmlPage() {
  const {
    data: watchlist,
    loading,
    error,
  } = usePolling<WatchlistEntry[]>(
    () => apiClient.get<WatchlistEntry[]>("/api/aml/watchlist"),
    []
  );

  const [fullName, setFullName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [result, setResult] = useState<ScreenResult | null>(null);

  const columns: Column<WatchlistEntry>[] = [
    { key: "full_name", header: "Full Name" },
    { key: "entity_type", header: "Entity Type" },
    { key: "country", header: "Country" },
    { key: "list_source", header: "List Source", mono: true },
  ];

  async function handleScreen(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setResult(null);
    if (!fullName.trim()) {
      setFormError("Please enter a name to screen.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiClient.post<ScreenResult>("/api/aml/screen", {
        full_name: fullName,
      });
      setResult(res);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to screen name.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="AML"
      description="Anti-money laundering name screening"
    >
      <div className="flex flex-col gap-6">
        <div className="rounded-lg border border-yellow-500/40 bg-yellow-500/10 p-4 text-sm text-yellow-300">
          <strong className="font-semibold">Demo data notice:</strong> This module
          uses a DEMO watchlist for simulation purposes only. It is not a real
          sanctions or PEP list.
        </div>

        <Card title="Name Screening">
          <form onSubmit={handleScreen} className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Label>Full Name</Label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Jane Doe"
                required
              />
            </div>
            <div>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Screening..." : "Screen Name"}
              </Button>
            </div>
          </form>
          {formError && <p className="mt-3 text-sm text-red-400">{formError}</p>}

          {result && (
            <div className="mt-4 rounded-lg border border-[#1e2530] bg-[#11161d] p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-200">
                Screening Result
              </h4>
              <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">
                    Query Name
                  </dt>
                  <dd className="text-slate-300">{result.query_name}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">
                    Matched Name
                  </dt>
                  <dd className="text-slate-300">{result.matched_name || "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">
                    Match Score
                  </dt>
                  <dd className="mono text-slate-300">
                    {result.match_score.toFixed(2)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">
                    List Source
                  </dt>
                  <dd className="mono text-slate-300">{result.list_source || "—"}</dd>
                </div>
              </dl>
            </div>
          )}
        </Card>

        <Card title="DEMO Watchlist">
          <DataTable
            columns={columns}
            rows={watchlist ?? []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="Watchlist is empty."
          />
        </Card>
      </div>
    </PageShell>
  );
}
