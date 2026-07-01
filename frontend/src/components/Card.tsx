import React from "react";

export function Card({
  children,
  className = "",
  title,
  action,
}: {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-lg border border-[#1e2530] bg-[#0d1117] ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-[#1e2530] px-4 py-3">
          {title && (
            <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
          )}
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

export function StatCard({
  label,
  value,
  accent,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  accent?: "critical" | "high" | "medium" | "low" | "default";
  sub?: string;
}) {
  const accentColor =
    {
      critical: "text-red-400",
      high: "text-orange-400",
      medium: "text-yellow-400",
      low: "text-blue-400",
      default: "text-slate-100",
    }[accent || "default"] || "text-slate-100";

  return (
    <div className="rounded-lg border border-[#1e2530] bg-[#0d1117] p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className={`mt-2 text-3xl font-bold ${accentColor}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}
