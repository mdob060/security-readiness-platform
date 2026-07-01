"use client";

import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { usePolling } from "@/hooks/usePolling";
import { apiClient } from "@/lib/apiClient";

interface HoneypotPorts {
  listeners: { port: number; service: string }[];
}

interface HoneypotEvent {
  id: number;
  listener_port: number;
  service_name: string;
  source_ip: string;
  source_port: number;
  payload_sample: string;
  created_at: string;
}

export default function HoneypotPage() {
  const {
    data: ports,
    loading: portsLoading,
    error: portsError,
  } = usePolling(() => apiClient.get<HoneypotPorts>("/api/honeypot/ports"), []);

  const {
    data: events,
    loading: eventsLoading,
    error: eventsError,
  } = usePolling(
    () => apiClient.get<HoneypotEvent[]>("/api/honeypot/events"),
    []
  );

  const columns: Column<HoneypotEvent>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "listener_port", header: "Port", mono: true },
    { key: "service_name", header: "Service" },
    { key: "source_ip", header: "Source IP", mono: true },
    { key: "source_port", header: "Source Port", mono: true },
    {
      key: "payload_sample",
      header: "Payload Sample",
      render: (row) => (
        <div className="mono max-h-24 max-w-xl overflow-y-auto whitespace-pre-wrap break-all rounded border border-[#1e2530] bg-black/40 px-2 py-1 text-xs text-slate-400">
          {row.payload_sample || "—"}
        </div>
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
      title="Honeypot"
      description="Live decoy service listeners and captured intrusion attempts — auto-refreshing every 10s"
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Active Listeners">
          {portsLoading && (
            <div className="py-4 text-center text-sm text-slate-500">
              Loading...
            </div>
          )}
          {!portsLoading && portsError && (
            <div className="py-4 text-center text-sm text-red-400">
              {portsError}
            </div>
          )}
          {!portsLoading &&
            !portsError &&
            (!ports || ports.listeners.length === 0) && (
              <div className="py-4 text-center text-sm text-slate-500">
                No listeners configured.
              </div>
            )}
          {!portsLoading && !portsError && ports && ports.listeners.length > 0 && (
            <div className="flex flex-wrap gap-3">
              {ports.listeners.map((l) => (
                <div
                  key={l.port}
                  className="flex items-center gap-2 rounded-md border border-[#1e2530] bg-[#11161d] px-3 py-2"
                >
                  <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-medium uppercase text-slate-300">
                    {l.service}
                  </span>
                  <span className="mono text-xs text-slate-500">
                    :{l.port}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Captured Events">
          <DataTable
            columns={columns}
            rows={events || []}
            keyField="id"
            loading={eventsLoading}
            error={eventsError}
            emptyMessage="No honeypot events captured yet."
          />
        </Card>
      </div>
    </PageShell>
  );
}
