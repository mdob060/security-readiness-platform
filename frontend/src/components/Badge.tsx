import React from "react";

const severityClasses: Record<string, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/40",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/40",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/40",
  low: "bg-blue-500/15 text-blue-400 border-blue-500/40",
  info: "bg-slate-500/15 text-slate-300 border-slate-500/40",

  open: "bg-red-500/15 text-red-400 border-red-500/40",
  acknowledged: "bg-yellow-500/15 text-yellow-400 border-yellow-500/40",
  closed: "bg-slate-500/15 text-slate-400 border-slate-500/40",
  pending: "bg-yellow-500/15 text-yellow-400 border-yellow-500/40",
  approved: "bg-green-500/15 text-green-400 border-green-500/40",
  rejected: "bg-red-500/15 text-red-400 border-red-500/40",
  revoked: "bg-slate-500/15 text-slate-400 border-slate-500/40",
  queued: "bg-slate-500/15 text-slate-300 border-slate-500/40",
  running: "bg-blue-500/15 text-blue-400 border-blue-500/40",
  completed: "bg-green-500/15 text-green-400 border-green-500/40",
  failed: "bg-red-500/15 text-red-400 border-red-500/40",
  compliant: "bg-green-500/15 text-green-400 border-green-500/40",
  pass: "bg-green-500/15 text-green-400 border-green-500/40",
  fail: "bg-red-500/15 text-red-400 border-red-500/40",
  gap: "bg-orange-500/15 text-orange-400 border-orange-500/40",
  not_assessed: "bg-slate-500/15 text-slate-400 border-slate-500/40",
  unknown: "bg-slate-500/15 text-slate-400 border-slate-500/40",
};

export function Badge({
  children,
  variant,
}: {
  children: React.ReactNode;
  variant?: string;
}) {
  const key = (variant || "info").toLowerCase();
  const cls = severityClasses[key] || severityClasses.info;
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${cls}`}
    >
      {children}
    </span>
  );
}
