"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Label, Select } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Controller {
  id: number;
  name: string;
  protocol: string;
  ip_address: string | null;
  status: string;
}

interface ScadaAlert {
  id: number;
  controller_id: number;
  description: string;
  severity: string;
  created_at: string;
}

const PROTOCOLS = ["modbus", "dnp3", "opcua"];

export default function OtScadaPage() {
  const { isAnalystOrAbove } = useAuth();

  const {
    data: controllers,
    loading: controllersLoading,
    error: controllersError,
    refetch: refetchControllers,
  } = usePolling<Controller[]>(
    () => apiClient.get<Controller[]>("/api/ot-scada/controllers"),
    []
  );

  const {
    data: alerts,
    loading: alertsLoading,
    error: alertsError,
  } = usePolling<ScadaAlert[]>(
    () => apiClient.get<ScadaAlert[]>("/api/ot-scada/alerts"),
    []
  );

  const [ctrlForm, setCtrlForm] = useState({ name: "", protocol: "modbus", ip_address: "" });
  const [ctrlSubmitting, setCtrlSubmitting] = useState(false);
  const [ctrlError, setCtrlError] = useState<string | null>(null);
  const [ctrlSuccess, setCtrlSuccess] = useState<string | null>(null);

  const [readingForm, setReadingForm] = useState({
    controller_id: "",
    metric: "",
    value: "",
    unit: "",
  });
  const [readingSubmitting, setReadingSubmitting] = useState(false);
  const [readingError, setReadingError] = useState<string | null>(null);
  const [readingSuccess, setReadingSuccess] = useState<string | null>(null);

  const controllerColumns: Column<Controller>[] = [
    { key: "name", header: "Name" },
    { key: "protocol", header: "Protocol" },
    { key: "ip_address", header: "IP Address", mono: true },
    { key: "status", header: "Status", badge: true },
  ];

  const alertColumns: Column<ScadaAlert>[] = [
    { key: "controller_id", header: "Controller ID", mono: true },
    { key: "description", header: "Description" },
    { key: "severity", header: "Severity", badge: true },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  async function handleCreateController(e: React.FormEvent) {
    e.preventDefault();
    setCtrlError(null);
    setCtrlSuccess(null);
    if (!ctrlForm.name) {
      setCtrlError("Name is required.");
      return;
    }
    setCtrlSubmitting(true);
    try {
      await apiClient.post<Controller>("/api/ot-scada/controllers", {
        name: ctrlForm.name,
        protocol: ctrlForm.protocol,
        ip_address: ctrlForm.ip_address || undefined,
      });
      setCtrlSuccess("Controller added.");
      setCtrlForm({ name: "", protocol: "modbus", ip_address: "" });
      refetchControllers();
    } catch (err) {
      setCtrlError(err instanceof ApiError ? err.message : "Failed to add controller.");
    } finally {
      setCtrlSubmitting(false);
    }
  }

  async function handleSubmitReading(e: React.FormEvent) {
    e.preventDefault();
    setReadingError(null);
    setReadingSuccess(null);
    const valueNum = Number(readingForm.value);
    if (!readingForm.controller_id || !readingForm.metric || readingForm.value === "" || Number.isNaN(valueNum)) {
      setReadingError("Please fill in all required fields with valid values.");
      return;
    }
    setReadingSubmitting(true);
    try {
      await apiClient.post("/api/ot-scada/readings", {
        controller_id: Number(readingForm.controller_id),
        metric: readingForm.metric,
        value: valueNum,
        unit: readingForm.unit || undefined,
      });
      setReadingSuccess("Sensor reading submitted.");
      setReadingForm({ controller_id: readingForm.controller_id, metric: "", value: "", unit: "" });
    } catch (err) {
      setReadingError(err instanceof ApiError ? err.message : "Failed to submit reading.");
    } finally {
      setReadingSubmitting(false);
    }
  }

  return (
    <PageShell
      title="OT / SCADA"
      description="Industrial control system monitoring"
    >
      <div className="flex flex-col gap-6">
        {isAnalystOrAbove && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card title="Add Controller">
              <form onSubmit={handleCreateController} className="flex flex-col gap-4">
                <div>
                  <Label>Name</Label>
                  <Input
                    value={ctrlForm.name}
                    onChange={(e) => setCtrlForm({ ...ctrlForm, name: e.target.value })}
                    placeholder="PLC-01"
                    required
                  />
                </div>
                <div>
                  <Label>Protocol</Label>
                  <Select
                    value={ctrlForm.protocol}
                    onChange={(e) => setCtrlForm({ ...ctrlForm, protocol: e.target.value })}
                  >
                    {PROTOCOLS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </Select>
                </div>
                <div>
                  <Label>IP Address (optional)</Label>
                  <Input
                    value={ctrlForm.ip_address}
                    onChange={(e) => setCtrlForm({ ...ctrlForm, ip_address: e.target.value })}
                    placeholder="10.0.0.5"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <Button type="submit" disabled={ctrlSubmitting}>
                    {ctrlSubmitting ? "Adding..." : "Add Controller"}
                  </Button>
                  {ctrlError && <span className="text-sm text-red-400">{ctrlError}</span>}
                  {ctrlSuccess && <span className="text-sm text-green-400">{ctrlSuccess}</span>}
                </div>
              </form>
            </Card>

            <Card title="Submit Sensor Reading">
              <form onSubmit={handleSubmitReading} className="flex flex-col gap-4">
                <div>
                  <Label>Controller</Label>
                  <Select
                    value={readingForm.controller_id}
                    onChange={(e) => setReadingForm({ ...readingForm, controller_id: e.target.value })}
                    required
                  >
                    <option value="">Select a controller...</option>
                    {(controllers ?? []).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} (#{c.id})
                      </option>
                    ))}
                  </Select>
                </div>
                <div>
                  <Label>Metric</Label>
                  <Input
                    value={readingForm.metric}
                    onChange={(e) => setReadingForm({ ...readingForm, metric: e.target.value })}
                    placeholder="temperature"
                    required
                  />
                </div>
                <div>
                  <Label>Value</Label>
                  <Input
                    type="number"
                    value={readingForm.value}
                    onChange={(e) => setReadingForm({ ...readingForm, value: e.target.value })}
                    placeholder="72.5"
                    required
                  />
                </div>
                <div>
                  <Label>Unit (optional)</Label>
                  <Input
                    value={readingForm.unit}
                    onChange={(e) => setReadingForm({ ...readingForm, unit: e.target.value })}
                    placeholder="C"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <Button type="submit" disabled={readingSubmitting}>
                    {readingSubmitting ? "Submitting..." : "Submit Reading"}
                  </Button>
                  {readingError && <span className="text-sm text-red-400">{readingError}</span>}
                  {readingSuccess && <span className="text-sm text-green-400">{readingSuccess}</span>}
                </div>
              </form>
            </Card>
          </div>
        )}

        <Card title="Controllers">
          <DataTable
            columns={controllerColumns}
            rows={controllers ?? []}
            keyField="id"
            loading={controllersLoading}
            error={controllersError}
            emptyMessage="No controllers registered."
          />
        </Card>

        <Card title="Alerts">
          <DataTable
            columns={alertColumns}
            rows={alerts ?? []}
            keyField="id"
            loading={alertsLoading}
            error={alertsError}
            emptyMessage="No alerts."
          />
        </Card>
      </div>
    </PageShell>
  );
}
