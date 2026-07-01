"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";

interface SettingModule {
  id: number;
  module_key: string;
  enabled: boolean;
  updated_at: string;
}

function ToggleSwitch({
  enabled,
  disabled,
  onToggle,
}: {
  enabled: boolean;
  disabled?: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onToggle}
      aria-pressed={enabled}
      className={`relative h-6 w-11 shrink-0 rounded-full border transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
        enabled
          ? "border-green-500/40 bg-green-500/70"
          : "border-[#1e2530] bg-[#1a2029]"
      }`}
    >
      <span
        className={`absolute top-0.5 h-4.5 w-4.5 rounded-full bg-white transition-transform ${
          enabled ? "translate-x-[22px]" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const { isAdmin } = useAuth();
  const [updatingKey, setUpdatingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    data: settings,
    loading,
    error: loadError,
    refetch,
  } = usePolling(() => apiClient.get<SettingModule[]>("/api/settings"), [], {
    intervalMs: 20000,
  });

  async function handleToggle(mod: SettingModule) {
    setUpdatingKey(mod.module_key);
    setError(null);
    try {
      await apiClient.patch(`/api/settings/${mod.module_key}`, {
        enabled: !mod.enabled,
      });
      refetch();
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Failed to update module setting"
      );
    } finally {
      setUpdatingKey(null);
    }
  }

  return (
    <PageShell
      title="Settings"
      description="Enable or disable platform modules"
    >
      <Card title="Modules">
        {error && (
          <div className="mb-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}
        {loading && (
          <div className="py-4 text-center text-sm text-slate-500">
            Loading...
          </div>
        )}
        {!loading && loadError && (
          <div className="py-4 text-center text-sm text-red-400">
            {loadError}
          </div>
        )}
        {!loading && !loadError && (!settings || settings.length === 0) && (
          <div className="py-4 text-center text-sm text-slate-500">
            No modules configured.
          </div>
        )}
        {!loading && !loadError && settings && settings.length > 0 && (
          <ul className="flex flex-col divide-y divide-[#151b23]">
            {settings
              .slice()
              .sort((a, b) => a.module_key.localeCompare(b.module_key))
              .map((mod) => (
                <li
                  key={mod.id}
                  className="flex items-center justify-between gap-4 py-3"
                >
                  <div>
                    <div className="text-sm text-slate-200">
                      {mod.module_key}
                    </div>
                    <div className="mt-0.5 mono text-xs text-slate-600">
                      updated {new Date(mod.updated_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={mod.enabled ? "compliant" : "not_assessed"}>
                      {mod.enabled ? "Enabled" : "Disabled"}
                    </Badge>
                    {isAdmin ? (
                      <ToggleSwitch
                        enabled={mod.enabled}
                        disabled={updatingKey === mod.module_key}
                        onToggle={() => handleToggle(mod)}
                      />
                    ) : (
                      <ToggleSwitch enabled={mod.enabled} disabled onToggle={() => {}} />
                    )}
                  </div>
                </li>
              ))}
          </ul>
        )}
        {!isAdmin && (
          <div className="mt-3 text-xs text-slate-500">
            Admin role required to toggle modules.
          </div>
        )}
      </Card>
    </PageShell>
  );
}
