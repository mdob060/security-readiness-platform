"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Input, Label } from "@/components/Button";
import { RoleGate } from "@/components/RoleGate";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Tenant {
  id: number;
  name: string;
  sector: string | null;
  is_active: boolean;
  created_at: string;
}

export default function TenantsPage() {
  const [name, setName] = useState("");
  const [sector, setSector] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    data: tenants,
    loading,
    error,
    refetch,
  } = usePolling(() => apiClient.get<Tenant[]>("/api/tenants"), [], {
    intervalMs: 20000,
  });

  async function handleAddTenant() {
    if (!name.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await apiClient.post("/api/tenants", {
        name: name.trim(),
        sector: sector.trim() || undefined,
      });
      setName("");
      setSector("");
      refetch();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "Failed to add tenant");
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<Tenant>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "name", header: "Name" },
    {
      key: "sector",
      header: "Sector",
      render: (row) => row.sector || "—",
    },
    {
      key: "is_active",
      header: "Active",
      render: (row) => (
        <Badge variant={row.is_active ? "compliant" : "not_assessed"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
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
    <PageShell title="Tenants" description="Multi-tenant organization management">
      <div className="grid grid-cols-1 gap-4">
        <Card title="Tenants">
          <DataTable
            columns={columns}
            rows={tenants || []}
            keyField="id"
            loading={loading}
            error={error}
            emptyMessage="No tenants found."
          />
        </Card>

        <RoleGate
          allow={["admin"]}
          fallback={
            <div className="text-xs text-slate-500">
              Admin role required to add tenants.
            </div>
          }
        >
          <Card title="Add Tenant">
            {formError && (
              <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {formError}
              </div>
            )}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <Label>Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Tenant name"
                />
              </div>
              <div>
                <Label>Sector (optional)</Label>
                <Input
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  placeholder="e.g. banking, healthcare"
                />
              </div>
            </div>
            <div className="mt-3 flex justify-end">
              <Button onClick={handleAddTenant} disabled={submitting || !name.trim()}>
                {submitting ? "Adding..." : "Add Tenant"}
              </Button>
            </div>
          </Card>
        </RoleGate>
      </div>
    </PageShell>
  );
}
