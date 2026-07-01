"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card, StatCard } from "@/components/Card";
import { DataTable, type Column } from "@/components/DataTable";
import { Button, Input, Textarea, Label } from "@/components/Button";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface CampaignResponse {
  id?: number;
  [key: string]: unknown;
}

interface SessionCampaign {
  id: number | string;
  name: string;
  template: string;
  targetCount: number;
}

interface CampaignStats {
  total_targets: number;
  clicked: number;
  click_rate: number;
}

export default function PhishingPage() {
  const { isAnalystOrAbove } = useAuth();

  // Create campaign form state
  const [name, setName] = useState("");
  const [template, setTemplate] = useState("");
  const [targetEmailsRaw, setTargetEmailsRaw] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccessId, setCreateSuccessId] = useState<number | string | null>(
    null
  );

  // Session-local campaign history
  const [sessionCampaigns, setSessionCampaigns] = useState<SessionCampaign[]>(
    []
  );

  // Stats state (used both for auto-fetch after creation and manual lookup)
  const [statsCampaignId, setStatsCampaignId] = useState("");
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [statsForId, setStatsForId] = useState<string | number | null>(null);

  function parseEmails(raw: string): string[] {
    return raw
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  async function fetchStats(campaignId: string | number) {
    setStatsLoading(true);
    setStatsError(null);
    try {
      const result = await apiClient.get<CampaignStats>(
        `/api/phishing/campaigns/${campaignId}/stats`
      );
      setStats(result);
      setStatsForId(campaignId);
    } catch (e) {
      setStatsError(
        e instanceof ApiError ? e.message : "Failed to fetch campaign stats"
      );
      setStats(null);
      setStatsForId(null);
    } finally {
      setStatsLoading(false);
    }
  }

  async function handleCreateCampaign() {
    const targetEmails = parseEmails(targetEmailsRaw);
    if (!name.trim() || !template.trim() || targetEmails.length === 0) return;

    setSubmitting(true);
    setCreateError(null);
    setCreateSuccessId(null);
    try {
      const result = await apiClient.post<CampaignResponse>(
        "/api/phishing/campaigns",
        {
          name: name.trim(),
          template: template.trim(),
          target_emails: targetEmails,
        }
      );

      const newId = result && typeof result === "object" ? result.id : undefined;

      setSessionCampaigns((prev) => [
        {
          id: newId ?? `local-${prev.length}`,
          name: name.trim(),
          template: template.trim(),
          targetCount: targetEmails.length,
        },
        ...prev,
      ]);

      if (newId !== undefined && newId !== null) {
        setCreateSuccessId(newId);
        setStatsCampaignId(String(newId));
        fetchStats(newId);
      }

      setName("");
      setTemplate("");
      setTargetEmailsRaw("");
    } catch (e) {
      setCreateError(
        e instanceof ApiError ? e.message : "Failed to create campaign"
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleManualLookup() {
    if (!statsCampaignId.trim()) return;
    fetchStats(statsCampaignId.trim());
  }

  const sessionColumns: Column<SessionCampaign>[] = [
    { key: "id", header: "ID", mono: true, width: "80px" },
    { key: "name", header: "Name" },
    { key: "template", header: "Template" },
    { key: "targetCount", header: "Targets", mono: true, width: "90px" },
  ];

  return (
    <PageShell
      title="Phishing Simulation"
      description="Create phishing awareness campaigns and review click-through stats"
    >
      <div className="grid grid-cols-1 gap-4">
        {isAnalystOrAbove ? (
          <Card title="Create Campaign">
            {createError && (
              <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {createError}
              </div>
            )}
            {createSuccessId !== null && (
              <div className="mb-3 rounded-md border border-green-500/40 bg-green-500/10 px-3 py-2 text-sm text-green-400">
                Campaign created (id: {String(createSuccessId)}).
              </div>
            )}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <Label>Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Q3 Security Awareness"
                />
              </div>
              <div>
                <Label>Template</Label>
                <Input
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                  placeholder="e.g. password-reset"
                />
              </div>
              <div className="sm:col-span-2">
                <Label>Target Emails (one per line or comma-separated)</Label>
                <Textarea
                  rows={4}
                  value={targetEmailsRaw}
                  onChange={(e) => setTargetEmailsRaw(e.target.value)}
                  placeholder={"alice@example.com\nbob@example.com"}
                />
              </div>
            </div>
            <div className="mt-3 flex justify-end">
              <Button
                onClick={handleCreateCampaign}
                disabled={
                  submitting ||
                  !name.trim() ||
                  !template.trim() ||
                  parseEmails(targetEmailsRaw).length === 0
                }
              >
                {submitting ? "Creating..." : "Create Campaign"}
              </Button>
            </div>
          </Card>
        ) : (
          <div className="text-xs text-slate-500">
            Viewer role: creating phishing campaigns is disabled.
          </div>
        )}

        <Card title="Look Up Campaign Stats by ID">
          <div className="flex items-end gap-3">
            <div className="max-w-[160px] flex-1">
              <Label>Campaign ID</Label>
              <Input
                type="number"
                value={statsCampaignId}
                onChange={(e) => setStatsCampaignId(e.target.value)}
                placeholder="e.g. 1"
              />
            </div>
            <Button
              variant="secondary"
              onClick={handleManualLookup}
              disabled={statsLoading || !statsCampaignId.trim()}
            >
              {statsLoading ? "Fetching..." : "Fetch Stats"}
            </Button>
          </div>

          {statsError && (
            <div className="mt-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {statsError}
            </div>
          )}

          {stats && !statsError && (
            <div className="mt-4">
              <div className="mb-2 text-xs text-slate-500">
                Stats for campaign #{String(statsForId)}
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <StatCard label="Total Targets" value={stats.total_targets} />
                <StatCard label="Clicked" value={stats.clicked} />
                <StatCard
                  label="Click Rate"
                  value={`${stats.click_rate.toFixed(1)}%`}
                />
              </div>
            </div>
          )}
        </Card>

        <Card title="Session Campaign History">
          <DataTable
            columns={sessionColumns}
            rows={sessionCampaigns}
            keyField="id"
            emptyMessage="No campaigns created this session."
          />
        </Card>
      </div>
    </PageShell>
  );
}
