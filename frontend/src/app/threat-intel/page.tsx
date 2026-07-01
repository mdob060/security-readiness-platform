"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Select, Label } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface ThreatActor {
  id: number;
  name: string;
  aliases: string | null;
  origin: string | null;
  motivation: string | null;
  description: string | null;
}

interface Ioc {
  id: number;
  ioc_type: string;
  value: string;
  threat_actor_id: number | null;
  confidence: number | null;
  source: string | null;
  created_at: string;
}

const IOC_TYPES = ["ip", "domain", "hash", "url"];

export default function ThreatIntelPage() {
  const { isAnalystOrAbove } = useAuth();

  const {
    data: actors,
    loading: actorsLoading,
    error: actorsError,
  } = usePolling(() => apiClient.get<ThreatActor[]>("/api/threat-intel/actors"), [], {
    intervalMs: 30000,
  });

  const {
    data: iocs,
    loading: iocsLoading,
    error: iocsError,
    refetch: refetchIocs,
  } = usePolling(() => apiClient.get<Ioc[]>("/api/threat-intel/iocs"), [], {
    intervalMs: 15000,
  });

  const [iocType, setIocType] = useState("ip");
  const [value, setValue] = useState("");
  const [threatActorId, setThreatActorId] = useState("");
  const [confidence, setConfidence] = useState("50");
  const [source, setSource] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const actorNameById = new Map<number, string>(
    (actors || []).map((a) => [a.id, a.name])
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!value.trim()) {
      setFormError("Value is required.");
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post("/api/threat-intel/iocs", {
        ioc_type: iocType,
        value: value.trim(),
        threat_actor_id: threatActorId ? Number(threatActorId) : null,
        confidence: confidence ? Number(confidence) : undefined,
        source: source.trim() || undefined,
      });
      setValue("");
      setThreatActorId("");
      setConfidence("50");
      setSource("");
      refetchIocs();
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : "Failed to create IOC."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const iocColumns: Column<Ioc>[] = [
    { key: "ioc_type", header: "Type", badge: true },
    { key: "value", header: "Value", mono: true },
    {
      key: "threat_actor_id",
      header: "Threat Actor",
      render: (row) =>
        row.threat_actor_id != null
          ? actorNameById.get(row.threat_actor_id) ?? `#${row.threat_actor_id}`
          : "—",
    },
    {
      key: "confidence",
      header: "Confidence",
      render: (row) => (row.confidence != null ? `${row.confidence}` : "—"),
    },
    {
      key: "source",
      header: "Source",
      render: (row) => row.source || "—",
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
      title="Threat Intelligence"
      description="Known threat actors and indicators of compromise (IOCs)"
    >
      <Card title="Threat Actors">
        {actorsLoading && (
          <div className="py-6 text-center text-sm text-slate-500">
            Loading...
          </div>
        )}
        {!actorsLoading && actorsError && (
          <div className="py-6 text-center text-sm text-red-400">
            {actorsError}
          </div>
        )}
        {!actorsLoading && !actorsError && (!actors || actors.length === 0) && (
          <div className="py-6 text-center text-sm text-slate-500">
            No threat actors on record.
          </div>
        )}
        {!actorsLoading && !actorsError && actors && actors.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {actors.map((actor) => (
              <div
                key={actor.id}
                className="rounded-lg border border-[#1e2530] bg-[#0d1117] p-4"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <h4 className="text-sm font-semibold text-slate-100">
                    {actor.name}
                  </h4>
                </div>
                {actor.aliases && (
                  <p className="mt-0.5 text-xs italic text-slate-500">
                    aka {actor.aliases}
                  </p>
                )}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {actor.origin && (
                    <Badge variant="info">{actor.origin}</Badge>
                  )}
                  {actor.motivation && (
                    <Badge variant="medium">{actor.motivation}</Badge>
                  )}
                </div>
                {actor.description && (
                  <p className="mt-2 text-xs text-slate-400">
                    {actor.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="mt-6">
        <Card title="Indicators of Compromise (IOCs)">
          <DataTable
            columns={iocColumns}
            rows={iocs || []}
            keyField="id"
            loading={iocsLoading}
            error={iocsError}
            emptyMessage="No IOCs recorded yet."
          />
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Add IOC">
          {isAnalystOrAbove ? (
            <form
              onSubmit={handleSubmit}
              className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5"
            >
              <div>
                <Label>Type</Label>
                <Select
                  value={iocType}
                  onChange={(e) => setIocType(e.target.value)}
                >
                  {IOC_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Value</Label>
                <Input
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="e.g. 1.2.3.4"
                  required
                />
              </div>
              <div>
                <Label>Threat Actor</Label>
                <Select
                  value={threatActorId}
                  onChange={(e) => setThreatActorId(e.target.value)}
                >
                  <option value="">None</option>
                  {(actors || []).map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Confidence</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={confidence}
                  onChange={(e) => setConfidence(e.target.value)}
                />
              </div>
              <div>
                <Label>Source</Label>
                <Input
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="optional"
                />
              </div>
              <div className="md:col-span-3 lg:col-span-5">
                {formError && (
                  <div className="mb-2 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                    {formError}
                  </div>
                )}
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Adding..." : "Add IOC"}
                </Button>
              </div>
            </form>
          ) : (
            <div className="text-sm text-slate-500">
              Viewers cannot add IOCs. Contact an analyst or admin.
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
