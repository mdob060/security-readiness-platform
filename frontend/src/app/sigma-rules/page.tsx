"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Button, Input, Textarea, Label } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface SigmaRule {
  id: number;
  name: string;
  yaml_definition: string;
  enabled: boolean;
  created_at: string;
}

export default function SigmaRulesPage() {
  const { isAnalystOrAbove } = useAuth();
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null);

  const [name, setName] = useState("");
  const [yamlDefinition, setYamlDefinition] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    data: rules,
    loading,
    error,
    refetch,
  } = usePolling(() => apiClient.get<SigmaRule[]>("/api/sigma-rules"), [], {
    intervalMs: 20000,
  });

  const selectedRule = rules?.find((r) => r.id === selectedRuleId) || null;

  async function handleSubmit() {
    if (!name.trim() || !yamlDefinition.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await apiClient.post("/api/sigma-rules", {
        name: name.trim(),
        yaml_definition: yamlDefinition,
        enabled,
      });
      setName("");
      setYamlDefinition("");
      setEnabled(true);
      refetch();
    } catch (e) {
      setFormError(
        e instanceof ApiError ? e.message : "Failed to create Sigma rule"
      );
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<SigmaRule>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "name", header: "Name" },
    {
      key: "enabled",
      header: "Status",
      render: (row) => (
        <span
          className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${
            row.enabled
              ? "bg-green-500/15 text-green-400 border-green-500/40"
              : "bg-slate-500/15 text-slate-400 border-slate-500/40"
          }`}
        >
          {row.enabled ? "Enabled" : "Disabled"}
        </span>
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
      title="Sigma Rules"
      description="Detection rule management for the SOC correlation engine"
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Sigma Rules">
          <DataTable
            columns={columns}
            rows={rules || []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No Sigma rules defined."
            onRowClick={(row) =>
              setSelectedRuleId(row.id === selectedRuleId ? null : row.id)
            }
          />
        </Card>

        {selectedRule && (
          <Card
            title={`YAML Definition — ${selectedRule.name}`}
            action={
              <button
                onClick={() => setSelectedRuleId(null)}
                className="text-xs text-slate-500 hover:text-slate-300"
              >
                Close
              </button>
            }
          >
            <pre className="mono text-xs whitespace-pre-wrap bg-black/40 border border-[#1e2530] rounded-md p-3 max-h-96 overflow-y-auto">
              {selectedRule.yaml_definition}
            </pre>
          </Card>
        )}

        {isAnalystOrAbove ? (
          <Card title="New Sigma Rule">
            {formError && (
              <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {formError}
              </div>
            )}
            <div className="flex flex-col gap-3">
              <div>
                <Label>Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Suspicious PowerShell Execution"
                />
              </div>
              <div>
                <Label>YAML Definition</Label>
                <Textarea
                  className="mono"
                  rows={10}
                  value={yamlDefinition}
                  onChange={(e) => setYamlDefinition(e.target.value)}
                  placeholder={
                    "title: My Rule\nlevel: medium\ndetection:\n  selection:\n    source: ...\n    event_type: ...\n"
                  }
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-[#1e2530] bg-[#11161d]"
                />
                Enabled
              </label>
              <div className="flex justify-end">
                <Button
                  onClick={handleSubmit}
                  disabled={submitting || !name.trim() || !yamlDefinition.trim()}
                >
                  {submitting ? "Creating..." : "Create Rule"}
                </Button>
              </div>
            </div>
          </Card>
        ) : (
          <div className="text-xs text-slate-500">
            Viewer role: creating Sigma rules is disabled.
          </div>
        )}
      </div>
    </PageShell>
  );
}
