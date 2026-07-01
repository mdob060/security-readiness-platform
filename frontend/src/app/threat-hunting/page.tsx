"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Button, Input, Select, Label } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface SecurityEvent {
  id: number;
  source: string;
  event_type: string;
  source_ip: string | null;
  detail: string;
  created_at: string;
}

interface SavedSearch {
  id: number;
  name: string;
  filters?: Record<string, unknown>;
  filters_json?: string;
  created_at?: string;
}

interface FilterForm {
  source: string;
  event_type: string;
  source_ip: string;
  severity: string;
  keyword: string;
}

const EMPTY_FORM: FilterForm = {
  source: "",
  event_type: "",
  source_ip: "",
  severity: "",
  keyword: "",
};

function buildFilterBody(form: FilterForm): Record<string, string> {
  const body: Record<string, string> = {};
  (Object.keys(form) as (keyof FilterForm)[]).forEach((key) => {
    const val = form[key].trim();
    if (val !== "") body[key] = val;
  });
  return body;
}

function parseSavedFilters(s: SavedSearch): Record<string, unknown> {
  if (s.filters && typeof s.filters === "object") return s.filters;
  if (s.filters_json) {
    try {
      return JSON.parse(s.filters_json) as Record<string, unknown>;
    } catch {
      return {};
    }
  }
  return {};
}

function formatFilters(filters: Record<string, unknown>): string {
  const parts = Object.entries(filters)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${String(v)}`);
  return parts.length > 0 ? parts.join(", ") : "(no filters)";
}

export default function ThreatHuntingPage() {
  const { isAnalystOrAbove } = useAuth();
  const [form, setForm] = useState<FilterForm>(EMPTY_FORM);
  const [results, setResults] = useState<SecurityEvent[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const {
    data: savedSearches,
    loading: savedLoading,
    error: savedError,
    refetch: refetchSaved,
  } = usePolling(() => apiClient.get<SavedSearch[]>("/api/threat-hunting/saved"), [], {
    intervalMs: 30000,
  });

  const updateField = (key: keyof FilterForm, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const runSearch = async () => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const body = buildFilterBody(form);
      const data = await apiClient.post<SecurityEvent[]>(
        "/api/threat-hunting/search",
        body
      );
      setResults(data);
      setHasSearched(true);
    } catch (e) {
      setSearchError(
        e instanceof ApiError ? e.message : "Failed to run search"
      );
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runSearch();
  };

  const saveSearch = async () => {
    if (!saveName.trim()) {
      setSaveError("Enter a name for this search first.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const body = buildFilterBody(form);
      await apiClient.post("/api/threat-hunting/saved", {
        name: saveName.trim(),
        filters: body,
      });
      setSaveName("");
      refetchSaved();
    } catch (e) {
      setSaveError(e instanceof ApiError ? e.message : "Failed to save search");
    } finally {
      setSaving(false);
    }
  };

  const applySavedSearch = (s: SavedSearch) => {
    const filters = parseSavedFilters(s);
    setForm({
      source: typeof filters.source === "string" ? filters.source : "",
      event_type: typeof filters.event_type === "string" ? filters.event_type : "",
      source_ip: typeof filters.source_ip === "string" ? filters.source_ip : "",
      severity: typeof filters.severity === "string" ? filters.severity : "",
      keyword: typeof filters.keyword === "string" ? filters.keyword : "",
    });
  };

  const resultColumns: Column<SecurityEvent>[] = [
    { key: "id", header: "ID", mono: true, width: "60px" },
    { key: "source", header: "Source" },
    { key: "event_type", header: "Event Type" },
    { key: "source_ip", header: "Source IP", mono: true },
    { key: "detail", header: "Detail" },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  const savedColumns: Column<SavedSearch>[] = [
    { key: "id", header: "ID", mono: true, width: "50px" },
    { key: "name", header: "Name" },
    {
      key: "filters",
      header: "Filters",
      render: (row) => (
        <span className="text-xs text-slate-400">
          {formatFilters(parseSavedFilters(row))}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) =>
        row.created_at ? new Date(row.created_at).toLocaleString() : "—",
    },
    {
      key: "actions",
      header: "",
      render: (row) => (
        <Button variant="ghost" onClick={() => applySavedSearch(row)}>
          Apply
        </Button>
      ),
    },
  ];

  return (
    <PageShell
      title="Threat Hunting"
      description="Search across security events with flexible filters and save useful searches for later"
    >
      <Card title="Search Filters">
        <form
          onSubmit={handleSubmit}
          className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          <div>
            <Label>Source</Label>
            <Input
              value={form.source}
              onChange={(e) => updateField("source", e.target.value)}
              placeholder="e.g. auth, banking, blue_team"
            />
          </div>
          <div>
            <Label>Event Type</Label>
            <Input
              value={form.event_type}
              onChange={(e) => updateField("event_type", e.target.value)}
              placeholder="e.g. bruteforce_attempt"
            />
          </div>
          <div>
            <Label>Source IP</Label>
            <Input
              value={form.source_ip}
              onChange={(e) => updateField("source_ip", e.target.value)}
              placeholder="e.g. 127.0.0.1"
            />
          </div>
          <div>
            <Label>Severity</Label>
            <Select
              value={form.severity}
              onChange={(e) => updateField("severity", e.target.value)}
            >
              <option value="">Any</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </Select>
          </div>
          <div className="md:col-span-2 lg:col-span-2">
            <Label>Keyword</Label>
            <Input
              value={form.keyword}
              onChange={(e) => updateField("keyword", e.target.value)}
              placeholder="Free-text search in event details"
            />
          </div>
          <div className="flex items-end gap-2 lg:col-span-3">
            <Button type="submit" disabled={searchLoading}>
              {searchLoading ? "Searching..." : "Search"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={searchLoading}
              onClick={() => setForm(EMPTY_FORM)}
            >
              Clear Filters
            </Button>
          </div>
        </form>

        {isAnalystOrAbove && (
          <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-[#1e2530] pt-4">
            <div className="flex-1 min-w-[200px]">
              <Label>Save current search as</Label>
              <Input
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="Search name"
              />
            </div>
            <Button
              type="button"
              variant="secondary"
              disabled={saving}
              onClick={saveSearch}
            >
              {saving ? "Saving..." : "Save this search"}
            </Button>
          </div>
        )}
        {saveError && (
          <div className="mt-2 text-xs text-red-400">{saveError}</div>
        )}
      </Card>

      <div className="mt-6">
        <Card title="Results">
          <DataTable
            columns={resultColumns}
            rows={results}
            keyField="id"
            loading={searchLoading}
            error={searchError}
            emptyMessage={
              hasSearched
                ? "No events matched your filters."
                : "Run a search to see results."
            }
          />
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Saved Searches">
          <DataTable
            columns={savedColumns}
            rows={savedSearches ?? []}
            keyField="id"
            loading={savedLoading}
            error={savedError}
            emptyMessage="No saved searches yet."
          />
        </Card>
      </div>
    </PageShell>
  );
}
