"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Select, Textarea, Label } from "@/components/Button";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface Incident {
  id: number;
  alert_id: number | null;
  title: string;
  severity: string;
  stage: string;
  assigned_to_id: number | null;
  created_at: string;
  closed_at: string | null;
}

interface TimelineEntry {
  id: number;
  note: string;
  author_id: number | null;
  created_at: string;
}

const STAGES = [
  "triage",
  "containment",
  "eradication",
  "recovery",
  "closed",
];

export default function IncidentsPage() {
  const { isAnalystOrAbove } = useAuth();
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(
    null
  );
  const [noteText, setNoteText] = useState("");
  const [submittingNote, setSubmittingNote] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [stageUpdating, setStageUpdating] = useState(false);
  const [stageError, setStageError] = useState<string | null>(null);

  const {
    data: incidents,
    loading: incidentsLoading,
    error: incidentsError,
    refetch: refetchIncidents,
  } = usePolling(() => apiClient.get<Incident[]>("/api/incidents"), [], {
    intervalMs: 15000,
  });

  const {
    data: timeline,
    loading: timelineLoading,
    error: timelineError,
    refetch: refetchTimeline,
  } = usePolling(
    () =>
      selectedIncidentId
        ? apiClient.get<TimelineEntry[]>(
            `/api/incidents/${selectedIncidentId}/timeline`
          )
        : Promise.resolve([]),
    [selectedIncidentId],
    { enabled: selectedIncidentId !== null, intervalMs: 15000 }
  );

  const selectedIncident =
    incidents?.find((i) => i.id === selectedIncidentId) || null;

  async function handleAddNote() {
    if (!selectedIncidentId || !noteText.trim()) return;
    setSubmittingNote(true);
    setNoteError(null);
    try {
      await apiClient.post(`/api/incidents/${selectedIncidentId}/timeline`, {
        note: noteText.trim(),
      });
      setNoteText("");
      refetchTimeline();
    } catch (e) {
      setNoteError(
        e instanceof ApiError ? e.message : "Failed to add timeline note"
      );
    } finally {
      setSubmittingNote(false);
    }
  }

  async function handleStageChange(newStage: string) {
    if (!selectedIncidentId) return;
    setStageUpdating(true);
    setStageError(null);
    try {
      await apiClient.patch(`/api/incidents/${selectedIncidentId}`, {
        stage: newStage,
      });
      refetchIncidents();
      refetchTimeline();
    } catch (e) {
      setStageError(
        e instanceof ApiError ? e.message : "Failed to update incident stage"
      );
    } finally {
      setStageUpdating(false);
    }
  }

  const columns: Column<Incident>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "title", header: "Title" },
    { key: "severity", header: "Severity", badge: true },
    { key: "stage", header: "Stage", badge: true },
    {
      key: "assigned_to_id",
      header: "Assigned To",
      mono: true,
      render: (row) => (row.assigned_to_id ? `#${row.assigned_to_id}` : "—"),
    },
    {
      key: "created_at",
      header: "Created At",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: "closed_at",
      header: "Closed At",
      mono: true,
      render: (row) =>
        row.closed_at ? new Date(row.closed_at).toLocaleString() : "—",
    },
  ];

  return (
    <PageShell
      title="Incidents"
      description="Incident response tracking and case management"
    >
      <div className="grid grid-cols-1 gap-4">
        <Card title="Incidents">
          <DataTable
            columns={columns}
            rows={incidents || []}
            keyField="id"
            loading={incidentsLoading}
            error={incidentsError}
            emptyMessage="No incidents recorded."
            onRowClick={(row) => setSelectedIncidentId(row.id)}
          />
        </Card>

        {selectedIncidentId !== null && (
          <Card
            title={
              selectedIncident
                ? `Incident #${selectedIncident.id} — ${selectedIncident.title}`
                : `Incident #${selectedIncidentId}`
            }
            action={
              <button
                onClick={() => setSelectedIncidentId(null)}
                className="text-xs text-slate-500 hover:text-slate-300"
              >
                Close
              </button>
            }
          >
            {selectedIncident && (
              <div className="mb-4 flex flex-wrap items-center gap-3">
                <Badge variant={selectedIncident.severity}>
                  {selectedIncident.severity}
                </Badge>
                <Badge variant={selectedIncident.stage}>
                  {selectedIncident.stage}
                </Badge>

                {isAnalystOrAbove ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs uppercase tracking-wide text-slate-500">
                      Stage:
                    </span>
                    <Select
                      value={selectedIncident.stage}
                      disabled={stageUpdating}
                      onChange={(e) => handleStageChange(e.target.value)}
                      className="w-40"
                    >
                      {STAGES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </Select>
                  </div>
                ) : (
                  <span className="text-xs text-slate-500">
                    Viewer role: stage changes are read-only.
                  </span>
                )}
              </div>
            )}

            {stageError && (
              <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {stageError}
              </div>
            )}

            <div className="mb-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Timeline
              </h4>
              {timelineLoading && (
                <div className="py-4 text-center text-sm text-slate-500">
                  Loading...
                </div>
              )}
              {!timelineLoading && timelineError && (
                <div className="py-4 text-center text-sm text-red-400">
                  {timelineError}
                </div>
              )}
              {!timelineLoading &&
                !timelineError &&
                (!timeline || timeline.length === 0) && (
                  <div className="py-4 text-center text-sm text-slate-500">
                    No timeline entries yet.
                  </div>
                )}
              {!timelineLoading && !timelineError && timeline && timeline.length > 0 && (
                <ul className="flex flex-col gap-3 border-l border-[#1e2530] pl-4">
                  {timeline
                    .slice()
                    .sort(
                      (a, b) =>
                        new Date(a.created_at).getTime() -
                        new Date(b.created_at).getTime()
                    )
                    .map((entry) => (
                      <li key={entry.id} className="relative">
                        <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-blue-500" />
                        <div className="text-sm text-slate-300">
                          {entry.note}
                        </div>
                        <div className="mt-0.5 mono text-xs text-slate-600">
                          {entry.author_id ? `author #${entry.author_id} — ` : ""}
                          {new Date(entry.created_at).toLocaleString()}
                        </div>
                      </li>
                    ))}
                </ul>
              )}
            </div>

            {isAnalystOrAbove ? (
              <div>
                <Label>Add Timeline Note</Label>
                {noteError && (
                  <div className="mb-2 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                    {noteError}
                  </div>
                )}
                <Textarea
                  rows={3}
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Describe the latest response action or finding..."
                />
                <div className="mt-2 flex justify-end">
                  <Button
                    onClick={handleAddNote}
                    disabled={submittingNote || !noteText.trim()}
                  >
                    {submittingNote ? "Adding..." : "Add Note"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500">
                Viewer role: adding timeline notes is disabled.
              </div>
            )}
          </Card>
        )}
      </div>
    </PageShell>
  );
}
