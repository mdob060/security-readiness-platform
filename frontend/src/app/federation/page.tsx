"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Label } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Peer {
  id: number;
  name: string;
  taxii_api_root: string | null;
  trusted: boolean;
  created_at: string;
}

export default function FederationPage() {
  const {
    data: peers,
    loading: peersLoading,
    error: peersError,
    refetch: refetchPeers,
  } = usePolling(() => apiClient.get<Peer[]>("/api/federation/peers"), [], {
    intervalMs: 20000,
  });

  const {
    data: collections,
    loading: collectionsLoading,
    error: collectionsError,
  } = usePolling(
    () => apiClient.get<unknown>("/api/federation/taxii2/collections"),
    [],
    { intervalMs: 30000 }
  );

  const [name, setName] = useState("");
  const [taxiiApiRoot, setTaxiiApiRoot] = useState("");
  const [trusted, setTrusted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!name.trim()) {
      setFormError("Name is required.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/federation/peers", {
        name: name.trim(),
        taxii_api_root: taxiiApiRoot.trim() || undefined,
        trusted,
      });
      setName("");
      setTaxiiApiRoot("");
      setTrusted(false);
      refetchPeers();
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : "Failed to create peer."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<Peer>[] = [
    { key: "name", header: "Name" },
    {
      key: "taxii_api_root",
      header: "TAXII API Root",
      mono: true,
      render: (row) => row.taxii_api_root || "—",
    },
    {
      key: "trusted",
      header: "Trusted",
      render: (row) => (
        <Badge variant={row.trusted ? "compliant" : "not_assessed"}>
          {row.trusted ? "Trusted" : "Untrusted"}
        </Badge>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  return (
    <PageShell
      title="Federation"
      description="Trusted peer organizations and STIX/TAXII sharing"
    >
      <Card title="Federation Peers">
        <DataTable
          columns={columns}
          rows={peers || []}
          keyField="id"
          loading={peersLoading}
          error={peersError}
          emptyMessage="No federation peers configured."
        />
      </Card>

      <div className="mt-6">
        <Card title="Add Peer">
          <RoleGate
            allow={["admin"]}
            fallback={
              <div className="text-sm text-slate-500">
                Admin only. Contact an administrator to add a peer.
              </div>
            }
          >
            <form
              onSubmit={handleSubmit}
              className="grid grid-cols-1 gap-4 md:grid-cols-3"
            >
              <div>
                <Label>Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Partner-ISAC"
                  required
                />
              </div>
              <div>
                <Label>TAXII API Root</Label>
                <Input
                  value={taxiiApiRoot}
                  onChange={(e) => setTaxiiApiRoot(e.target.value)}
                  placeholder="optional, e.g. https://peer.example/taxii2/"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={trusted}
                    onChange={(e) => setTrusted(e.target.checked)}
                    className="h-4 w-4 rounded border-[#1e2530] bg-[#11161d]"
                  />
                  Trusted
                </label>
              </div>
              <div className="md:col-span-3">
                {formError && (
                  <div className="mb-2 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                    {formError}
                  </div>
                )}
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Adding..." : "Add Peer"}
                </Button>
              </div>
            </form>
          </RoleGate>
        </Card>
      </div>

      <div className="mt-6">
        <Card title="TAXII Collections">
          {collectionsLoading && (
            <div className="py-6 text-center text-sm text-slate-500">
              Loading...
            </div>
          )}
          {!collectionsLoading && collectionsError && (
            <div className="py-6 text-center text-sm text-red-400">
              {collectionsError}
            </div>
          )}
          {!collectionsLoading && !collectionsError && (
            <pre className="mono text-xs whitespace-pre-wrap bg-black/40 border border-[#1e2530] rounded-md p-3 overflow-x-auto">
              {JSON.stringify(collections, null, 2)}
            </pre>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
